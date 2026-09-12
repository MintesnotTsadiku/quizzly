"""Site policy, private browser trials and account entitlements.

Guest is never an ownership identity. Only a hashed, HttpOnly browser capability
can authorize a trial's records. Quotas lock a durable row in the same database
transaction as creation, including writes through Frappe's document API.
"""

from __future__ import annotations

import hashlib
import secrets
from urllib.parse import urlparse

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, get_datetime, get_url, now_datetime, strip_html_tags

COOKIE = "gatherplay_trial"
PACK_TYPES = ("QZ Quiz", "GP Crowd Pack", "GP Cue Deck", "GP Draw Pack", "GP Game Pack")
SESSION_TYPES = ("GP Session", "QZ Session")


def settings():
	return frappe.get_cached_doc("GatherPlay Settings")


def digest(value):
	return hashlib.sha256(value.encode()).hexdigest()


def is_guest():
	return frappe.session.user == "Guest"


def same_origin():
	request = getattr(frappe.local, "request", None)
	if not request:
		return
	origin = request.headers.get("Origin") or request.headers.get("Referer")
	if not origin or urlparse(origin).netloc != request.host:
		frappe.throw("Open GatherPlay on this site before making changes.", frappe.PermissionError)


def trial_name():
	request = getattr(frappe.local, "request", None)
	token = request.cookies.get(COOKIE) if request else None
	return frappe.db.get_value("GatherPlay Access", {"principal": digest(token)}) if token else None


def get_access(create=False):
	user = frappe.session.user
	local_access = getattr(frappe.local, "gatherplay_access", None)
	if local_access and local_access[0] == user:
		return frappe.get_doc("GatherPlay Access", local_access[1])
	trial = trial_name()
	if not is_guest():
		name = frappe.db.get_value("GatherPlay Access", {"principal": digest("user:" + user)})
		if not name and create:
			# Account creation is serialized, including two tabs arriving together.
			with frappe.cache.lock("gp:account:" + digest(user), timeout=10):
				name = frappe.db.get_value("GatherPlay Access", {"principal": digest("user:" + user)})
				if not name:
					name = (
						frappe.get_doc(
							{
								"doctype": "GatherPlay Access",
								"principal": digest("user:" + user),
								"user": user,
							}
						)
						.insert(ignore_permissions=True)
						.name
					)
					frappe.db.commit()
		if name and trial and create:
			claim_trial(trial, name, user)
	else:
		name = trial
		if not name and create:
			same_origin()
			token = secrets.token_urlsafe(32)
			name = (
				frappe.get_doc(
					{
						"doctype": "GatherPlay Access",
						"principal": digest(token),
						"guest_expires": add_days(now_datetime(), settings().guest_days),
					}
				)
				.insert(ignore_permissions=True)
				.name
			)
			frappe.local.cookie_manager.set_cookie(
				COOKIE, token, httponly=True, samesite="Lax", max_age=86400 * int(settings().guest_days)
			)
	if name:
		frappe.local.gatherplay_access = (user, name)
		return frappe.get_doc("GatherPlay Access", name)
	return None


def claim_trial(trial, account, user):
	# Deterministic row lock order avoids competing claim deadlocks.
	for name in sorted([trial, account]):
		frappe.db.sql("select name from `tabGatherPlay Access` where name=%s for update", name)
	old = frappe.get_doc("GatherPlay Access", trial)
	if old.user or not old.guest_expires or get_datetime(old.guest_expires) < now_datetime():
		return
	current = frappe.get_doc("GatherPlay Access", account)
	period = now_datetime().strftime("%Y-%m")

	def monthly_used(doc, action):
		return int(doc.get(action + "_used") or 0) if doc.period == period else 0

	frappe.db.set_value(
		"GatherPlay Access",
		account,
		{
			"trial_hosts": current.trial_hosts + old.trial_hosts,
			"trial_packs": current.trial_packs + old.trial_packs,
			"hosts_used": monthly_used(current, "hosts") + monthly_used(old, "hosts"),
			"packs_used": monthly_used(current, "packs") + monthly_used(old, "packs"),
			"period": period,
		},
	)
	for dt in (*SESSION_TYPES, *PACK_TYPES):
		for row in frappe.get_all(dt, filters={"gatherplay_access": trial}, pluck="name"):
			values = {"gatherplay_access": account, "owner": user}
			if dt in SESSION_TYPES:
				values["host"] = user
			frappe.db.set_value(dt, row, values)
	frappe.db.set_value("GatherPlay Access", trial, "user", user)


def verified(access, policy):
	if is_guest():
		return False
	if not policy.require_verified_email:
		return True
	if policy.trust_existing_hosts and set(frappe.get_roles()) & {"Quiz Host", "System Manager"}:
		return True
	return bool(
		access
		and access.email_verified
		and access.verified_address == frappe.db.get_value("User", frappe.session.user, "email")
	)


def paid_receipt(access):
	if not access:
		return None
	rows = frappe.get_all(
		"GatherPlay Receipt",
		filters={
			"access": access.name,
			"status": ["in", ["Approved", "Provisional"]],
			"valid_until": [">", now_datetime()],
		},
		fields=["name", "status", "valid_until"],
		order_by="valid_until desc",
		limit=1,
	)
	return rows[0] if rows else None


def allowance(access, action, policy=None):
	# Match before_create: Administrator already bypasses site quotas.
	if frappe.session.user == "Administrator":
		return None, ""
	policy = policy or settings()
	used = int(access.get("trial_" + action) or 0) if access else 0
	if is_guest():
		if not policy.get("allow_guest_host" if action == "hosts" else "allow_guest_create"):
			return 0, "Sign in to continue. Guest access is disabled on this site."
		if access and (
			access.user or not access.guest_expires or get_datetime(access.guest_expires) < now_datetime()
		):
			return 0, "Your trial has ended. Sign in to keep playing."
		limit = int(policy.guest_host_limit if action == "hosts" else policy.guest_pack_limit)
		return max(0, limit - used), "Your guest trial is used up. Sign in and verify your email to continue."
	if not verified(access, policy):
		limit = int(policy.guest_host_limit if action == "hosts" else policy.guest_pack_limit)
		return max(0, limit - used), "Verify your email in Your access to keep creating and hosting."
	paid = policy.access_mode == "Paid" and paid_receipt(access)
	limit = int(
		policy.get(("paid_" if paid else "member_") + ("host_limit" if action == "hosts" else "pack_limit"))
		or 0
	)
	if policy.access_mode == "Community" and limit == 0:
		return None, ""
	monthly = (
		int(access.get(action + "_used") or 0)
		if access and access.period == now_datetime().strftime("%Y-%m")
		else 0
	)
	return max(
		0, limit - monthly
	), "Your allowance is used up. Visit Your access for the options on this site."


def consume(access, action):
	frappe.db.sql("select name from `tabGatherPlay Access` where name=%s for update", access.name)
	access.reload()
	remaining, reason = allowance(access, action)
	if remaining == 0:
		frappe.throw(reason, frappe.PermissionError)
	period = now_datetime().strftime("%Y-%m")
	if access.period != period:
		access.period, access.hosts_used, access.packs_used = period, 0, 0
	access.set(action + "_used", int(access.get(action + "_used") or 0) + 1)
	access.set("trial_" + action, int(access.get("trial_" + action) or 0) + 1)
	access.save(ignore_permissions=True)


def before_create(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate or frappe.session.user == "Administrator":
		return
	access = get_access(create=True)
	consume(access, "hosts" if doc.doctype in SESSION_TYPES else "packs")
	doc.gatherplay_access = access.name
	if doc.doctype in SESSION_TYPES:
		doc.host = frappe.session.user
	elif "System Manager" not in frappe.get_roles():
		doc.is_demo = 0
		doc.demo_key = None


def protect_pack(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate or "System Manager" in frappe.get_roles():
		return
	if doc.is_demo or doc.demo_key:
		frappe.throw("Only a site administrator can publish catalog packs.", frappe.PermissionError)
	if not doc.is_new():
		old = doc.get_doc_before_save()
		if old and old.gatherplay_access != doc.gatherplay_access:
			frappe.throw("Pack ownership cannot be changed.", frappe.PermissionError)


def authorize_host(doc):
	if not is_guest() and doc.host == frappe.session.user:
		doc.flags.ignore_permissions = True
		return doc
	access = get_access()
	if not access or access.user or not doc.gatherplay_access or access.name != doc.gatherplay_access:
		frappe.throw("This game belongs to another host.", frappe.PermissionError)
	if not access.guest_expires or get_datetime(access.guest_expires) < now_datetime():
		frappe.throw("This guest trial has expired. Sign in to continue.", frappe.PermissionError)
	doc.flags.ignore_permissions = True
	return doc


def host_filters():
	if not is_guest():
		return {"host": frappe.session.user}
	access = get_access()
	return {"host": "Guest", "gatherplay_access": access.name if access and not access.user else "__none__"}


def check_pack(doctype, name):
	doc = frappe.get_doc(doctype, name)
	if doc.is_demo:
		return
	access = get_access()
	if access and doc.gatherplay_access == access.name and (not is_guest() or not access.user):
		return
	if not is_guest():
		doc.check_permission("read")
		return
	frappe.throw("Choose a public pack or one you created.", frappe.PermissionError)


def check_join():
	if is_guest() and not settings().allow_guest_join:
		frappe.throw("This site requires players to sign in before joining.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def configuration() -> dict:
	p = settings()
	keys = (
		"product_name",
		"default_language",
		"tagline",
		"tagline_am",
		"intro",
		"intro_am",
		"accent_color",
		"logo",
		"enable_install",
		"access_mode",
		"allow_guest_join",
		"allow_guest_host",
		"allow_guest_create",
		"guest_host_limit",
		"guest_pack_limit",
		"require_verified_email",
		"plan_name",
		"price",
		"currency",
		"payment_instructions",
		"payment_instructions_am",
		"paid_host_limit",
		"paid_pack_limit",
		"plan_days",
		"optimistic_approval",
		"provisional_days",
	)
	return {
		**{key: p.get(key) for key in keys},
		"can_manage": not is_guest() and "System Manager" in frappe.get_roles(),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=60)
def my_access() -> dict:
	same_origin()
	a = get_access(create=True)
	return {
		"guest": is_guest(),
		"verified": verified(a, settings()),
		"hosts_remaining": allowance(a, "hosts")[0],
		"packs_remaining": allowance(a, "packs")[0],
		"host_message": allowance(a, "hosts")[1],
		"pack_message": allowance(a, "packs")[1],
		"paid": paid_receipt(a) if not is_guest() else None,
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60)
def guest_host(method: str, params: dict | str | None = None, legacy: bool = False) -> dict | None:
	"""Small explicit adapter. Never dispatch arbitrary dotted methods."""
	same_origin()
	allowed = {
		"create_session",
		"replay",
		"get_host_state",
		"start_session",
		"host_command",
		"end_session",
		"advance_room",
		"set_lobby_locked",
		"lock_lobby",
		"unlock_lobby",
		"kick_participant",
		"assign_teams",
		"rename_team",
		"recolor_team",
		"reassign_performer",
		"get_lobby",
		"set_auto_advance",
		"next_question",
		"skip_question",
		"list_quizzes",
		"pause",
		"resume",
		"advance",
		"skip",
		"previous",
	}
	if method not in allowed:
		frappe.throw("That host action is unavailable.", frappe.PermissionError)
	from quizzly import api as quiz_api
	from quizzly.games import api as game_api

	if method == "replay":
		from quizzly.batches import replay

		args = game_api.as_dict(params)
		return replay(session=args.get("session"), quiz=legacy, reset=args.get("reset", False))
	api = quiz_api if legacy else game_api
	if not hasattr(api, method):
		frappe.throw("Unknown host action")
	if method == "list_quizzes" and is_guest():
		return game_api.list_public_decks("quiz")
	args = game_api.as_dict(params)
	if method == "create_session" and is_guest():
		return create_guest_session(api, args)
	return getattr(api, method)(**args)


@rate_limit(limit=12, seconds=3600)
def create_guest_session(api, args):
	# An IP-based ceiling also applies when a visitor clears their trial cookie.
	return api.create_session(**args)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=3600)
def save_pack(title: str, prompts: list | str, name: str | None = None, language: str | None = None) -> dict:
	same_origin()
	a = get_access(create=True)
	if is_guest() and (
		a.user
		or not a.guest_expires
		or get_datetime(a.guest_expires) < now_datetime()
		or not settings().allow_guest_create
	):
		frappe.throw("Sign in to edit your packs.", frappe.PermissionError)
	rows = frappe.parse_json(prompts) if isinstance(prompts, str) else prompts
	if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
		frappe.throw("Add between 1 and 20 questions.")

	def clean(value, limit):
		if not isinstance(value, str):
			frappe.throw("Questions and choices must be text.")
		return strip_html_tags(value).strip()[:limit]

	items = []
	for row in rows:
		if (
			not isinstance(row, dict)
			or not isinstance(row.get("choices"), list)
			or not 2 <= len(row["choices"]) <= 4
		):
			frappe.throw("Each question needs two to four choices.")
		choices = [clean(c, 120) for c in row["choices"]]
		text = clean(row.get("text"), 300)
		if not text or any(not c for c in choices) or len(set(c.casefold() for c in choices)) != len(choices):
			frappe.throw("Use a question and distinct, nonempty choices.")
		items.append({"prompt_text": text, **{f"choice_{i + 1}": c for i, c in enumerate(choices)}})
	if name:
		doc = frappe.get_doc("GP Crowd Pack", name)
		if doc.gatherplay_access != a.name or doc.is_demo:
			frappe.throw("This pack belongs to another author.", frappe.PermissionError)
	else:
		doc = frappe.new_doc("GP Crowd Pack")
	if not name:
		from quizzly.localization import content_language

		doc.content_language = content_language(language)
	doc.title = clean(title, 100)
	if not doc.title:
		frappe.throw("Give your pack a title.")
	doc.set("prompts", items)
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def my_packs() -> list:
	a = get_access()
	if not a or (
		is_guest() and (a.user or not a.guest_expires or get_datetime(a.guest_expires) < now_datetime())
	):
		return []
	return frappe.get_all(
		"GP Crowd Pack",
		filters={"gatherplay_access": a.name},
		fields=["name", "title"],
		order_by="modified desc",
		limit=100,
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def load_pack(name: str) -> dict:
	a = get_access()
	if not a or name not in {p.name for p in my_packs()}:
		frappe.throw("This pack is not available to your account.", frappe.PermissionError)
	doc = frappe.get_doc("GP Crowd Pack", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"prompts": [
			{
				"text": row.prompt_text,
				"choices": [row.get(f"choice_{i}") for i in range(1, 5) if row.get(f"choice_{i}")],
			}
			for row in doc.prompts
		],
	}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=2, seconds=300)
def send_verification() -> dict:
	a = get_access(create=True)
	token = secrets.token_urlsafe(32)
	email = frappe.db.get_value("User", frappe.session.user, "email")
	a.verification_hash = digest(token)
	a.verification_expires = add_days(now_datetime(), 1)
	a.verified_address = email
	a.email_verified = 0
	a.save(ignore_permissions=True)
	url = get_url("/play/access") + "#verify=" + token
	frappe.sendmail(
		recipients=[email],
		subject="Verify your GatherPlay email",
		message=f'<p>Confirm your email to keep hosting.</p><p><a href="{url}">Verify email</a></p><p>This link expires in 24 hours. Open it while signed in to the same account.</p>',
	)
	return {"sent": True}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=300)
def verify_email(token: str) -> dict:
	a = get_access(create=True)
	if (
		not a.verification_hash
		or not secrets.compare_digest(digest(token), a.verification_hash)
		or get_datetime(a.verification_expires) < now_datetime()
		or a.verified_address != frappe.db.get_value("User", frappe.session.user, "email")
	):
		frappe.throw("That verification link is invalid or expired.")
	a.email_verified, a.verification_hash = 1, None
	a.save(ignore_permissions=True)
	return {"verified": True}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=5, seconds=3600)
def submit_receipt(reference: str, file_url: str) -> dict:
	p = settings()
	a = get_access(create=True)
	if p.access_mode != "Paid" or not verified(a, p):
		frappe.throw("Paid access requires a verified account on a paid site.", frappe.PermissionError)
	frappe.db.sql("select name from `tabGatherPlay Access` where name=%s for update", a.name)
	file_name = frappe.db.get_value(
		"File", {"file_url": file_url, "owner": frappe.session.user, "is_private": 1}
	)
	if not file_name:
		frappe.throw("Attach a private receipt uploaded by your account.", frappe.PermissionError)
	file = frappe.get_doc("File", file_name)
	if (
		file.attached_to_doctype
		or file.file_size > 5 * 1024 * 1024
		or not (file.file_name or "").lower().endswith((".png", ".jpg", ".jpeg", ".pdf"))
	):
		frappe.throw("Use an unattached PNG, JPEG or PDF receipt under 5 MB.")
	content = file.get_content()
	if isinstance(content, str):
		content = content.encode()
	if not (
		content.startswith(b"%PDF-")
		or content.startswith(b"\x89PNG\r\n\x1a\n")
		or content.startswith(b"\xff\xd8\xff")
	):
		frappe.throw("That file is not a supported receipt image or PDF.")
	ref = strip_html_tags(reference).strip().upper()
	if not 4 <= len(ref) <= 100:
		frappe.throw("Enter the payment reference (4-100 characters).")
	period = now_datetime().strftime("%Y-%m")
	previous = frappe.db.exists("GatherPlay Receipt", {"access": a.name, "period": period})
	provisional = bool(p.optimistic_approval and not previous)
	doc = frappe.get_doc(
		{
			"doctype": "GatherPlay Receipt",
			"access": a.name,
			"user": frappe.session.user,
			"reference": ref,
			"proof": file_url,
			"proof_digest": hashlib.sha256(content).hexdigest(),
			"amount": p.price,
			"currency": p.currency,
			"plan_name": p.plan_name,
			"period": period,
			"status": "Provisional" if provisional else "Pending",
			"valid_until": add_days(now_datetime(), p.provisional_days) if provisional else None,
		}
	).insert(ignore_permissions=True)
	file.reload()
	file.attached_to_doctype, file.attached_to_name = doc.doctype, doc.name
	file.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status, "valid_until": doc.valid_until}


@frappe.whitelist(methods=["POST"])
def my_receipts() -> list:
	return frappe.get_all(
		"GatherPlay Receipt",
		filters={"user": frappe.session.user},
		fields=["name", "status", "reference", "valid_until", "review_note"],
		order_by="creation desc",
		limit=20,
	)
