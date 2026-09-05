"""Real database policy checks. All test records roll back; no email is sent."""

import json
import os
import secrets
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import add_days, now_datetime

bench = Path(__file__).resolve().parents[4]
os.chdir(bench / "sites")
frappe.init(site="training.localhost", sites_path=str(bench / "sites"))
frappe.connect()
frappe.set_user("Administrator")
from frappe.utils.file_manager import save_file

from quizzly import access
from quizzly.games.api import create_session

checks = []
files = []


def passed(message):
	checks.append(message)
	print("PASS:", message)


def user(name, account=None):
	frappe.set_user(name)
	frappe.local.gatherplay_access = (name, account.name) if account else None


def denied(fn):
	try:
		fn()
	except (frappe.PermissionError, frappe.ValidationError):
		return
	raise AssertionError("Operation should have been denied")


try:
	suffix = secrets.token_hex(5)
	email = f"gp-policy-{suffix}@example.invalid"
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": "Policy QA",
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	member = frappe.get_doc(
		{"doctype": "GatherPlay Access", "principal": access.digest("user:" + email), "user": email}
	).insert(ignore_permissions=True)
	trial = frappe.get_doc(
		{
			"doctype": "GatherPlay Access",
			"principal": access.digest(suffix),
			"guest_expires": add_days(now_datetime(), 7),
		}
	).insert(ignore_permissions=True)
	policy = frappe.copy_doc(access.settings())
	policy.allow_guest_host = 1
	policy.allow_guest_create = 1
	policy.guest_host_limit = 2
	policy.guest_pack_limit = 1
	policy.access_mode = "Community"
	policy.require_verified_email = 1
	policy.trust_existing_hosts = 0
	with patch("quizzly.access.settings", return_value=policy):
		user("Guest", trial)
		first = create_session("common-ground", {"pack": "everyday"})
		second = create_session("common-ground", {"pack": "imagination"})
		denied(lambda: create_session("common-ground", {"pack": "everyday"}))
		assert frappe.db.count("GP Session", {"gatherplay_access": trial.name}) == 2
		passed("Guest quota is enforced by document creation, with two durable sessions")
		denied(
			lambda: frappe.get_doc(
				{
					"doctype": "GP Session",
					"host": "Administrator",
					"game_key": "common-ground",
					"status": "Lobby",
				}
			).insert(ignore_permissions=True)
		)
		passed("Direct document creation cannot bypass the guest quota")
		# Historical monthly usage must not leak into a new calendar month on claim.
		frappe.db.set_value("GatherPlay Access", member.name, {"period": "2000-01", "hosts_used": 19})
		user(email, member)
		access.claim_trial(trial.name, member.name, email)
		member.reload()
		assert member.trial_hosts == 2
		assert member.hosts_used == 2
		assert member.period == now_datetime().strftime("%Y-%m")
		assert frappe.db.get_value("GP Session", first["session"], "host") == email
		denied(lambda: create_session("common-ground", {"pack": "everyday"}))
		passed(
			"Account claim transfers ownership and retains consumed trial allowance; unverified hosting is denied"
		)
		with patch("frappe.sendmail") as send:
			access.send_verification()
			import re

			token = re.search(r'#verify=([^"<]+)', send.call_args.kwargs["message"]).group(1)
			denied(lambda: access.verify_email("invalid"))
			access.verify_email(token)
			denied(lambda: access.verify_email(token))
		member.reload()
		assert access.verified(member, policy)
		assert access.allowance(member, "hosts")[0] is None
		passed(
			"Email verification is account-bound, single-use and required before unlimited community access"
		)
		policy.access_mode = "Paid"
		policy.member_host_limit = 0
		policy.member_pack_limit = 0
		policy.price = 100
		policy.currency = "ETB"
		policy.payment_instructions = "Test transfer"
		policy.plan_days = 30
		policy.provisional_days = 3
		policy.optimistic_approval = 1
		assert access.allowance(member, "hosts")[0] == 0
		png = (Path(__file__).resolve().parents[2] / "quizzly/public/images/gatherplay-192.png").read_bytes()
		f = save_file(f"gp-policy-{suffix}.png", png, None, None, is_private=1)
		files.append(Path(f.get_full_path()))
		receipt = access.submit_receipt("QA-" + suffix, f.file_url)
		assert receipt["status"] == "Provisional"
		assert access.allowance(member, "hosts")[0] > 0
		passed("Private receipt grants expiring provisional access on paid sites")
		user("Administrator")
		doc = frappe.get_doc("GatherPlay Receipt", receipt["name"])
		doc.status = "Rejected"
		doc.review_note = "Verification test"
		doc.save()
		user(email, member)
		assert access.allowance(member, "hosts")[0] == 0
		denied(lambda: create_session("common-ground", {"pack": "everyday"}))
		assert access.authorize_host(frappe.get_doc("GP Session", first["session"]))
		passed("Rejection removes paid hosting entitlement while retaining control of an existing game")
		user("Administrator")
		doc.reload()
		doc.status = "Approved"
		doc.save()
		user(email, member)
		assert access.paid_receipt(member).status == "Approved"
		passed("Admin approval restores access and records the reviewer")
		user("Guest", trial)
		denied(lambda: access.authorize_host(frappe.get_doc("GP Session", first["session"])))
		assert access.my_packs() == []
		passed("Claimed guest capability cannot access the account's games or packs")
	Path(__file__).resolve().parents[2].joinpath("docs/access/evidence/backend-results.json").write_text(
		json.dumps({"passed": True, "checks": checks}, indent=2)
	)
finally:
	frappe.db.rollback()
	for path in files:
		if path.exists():
			path.unlink()
	frappe.destroy()
