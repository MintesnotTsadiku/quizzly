"""Durable selection and authorized, single-successor replay for a room's group."""

import random

import frappe
from frappe import _

from quizzly import access

EXCEPTIONS = {
	"escape-together": "Play all escape stages in their authored order.",
	"bracket-bash": "Play the complete tournament; entrants determine the match count.",
	"story-loom": "Story length is configurable; one story grows across its rounds. Start a new story to replay.",
	"grid-conquest": "Play three boards using the existing match rules.",
	"dots-and-boxes": "Complete the starter board.",
	"group-sudoku": "Complete the starter board.",
	"path-weaver": "Complete the starter board.",
	"hidden-picture": "Complete the starter board.",
	"quilt-puzzle": "Complete the starter board.",
}


def content_source(key, config):
	if key in EXCEPTIONS:
		return None, []
	pack = config.get("pack") or config.get("deck")
	if key == "common-ground":
		from quizzly.games.common_ground.game import PACKS

		return [key, pack, config.get("language", "en")], [str(i) for i in range(len(PACKS[pack]["prompts"]))]
	from quizzly.games.api import CONTENT_PREVIEWS

	preview = CONTENT_PREVIEWS.get(key)
	if not preview or not pack:
		return None, []
	language = frappe.db.get_value(preview["pack_doctype"], pack, "content_language") or "en"
	ids = frappe.get_all(
		preview["prompt_doctype"],
		filters={"parent": pack, "parenttype": preview["pack_doctype"]},
		pluck="name",
		order_by="idx asc",
	)
	return [key, pack, language], ids


def count_value(value, available, default=None):
	if value in (None, "", 0, "0"):
		return min(default or available, available)
	try:
		count = int(value)
		if isinstance(value, bool) or str(count) != str(value) or not 1 <= count <= available:
			raise ValueError
	except (ValueError, TypeError):
		frappe.throw(_("Choose a whole number between 1 and {0}.").format(available))
	return count


def draw(ids, count, used):
	remaining = [i for i in ids if i not in set(used)]
	if not remaining:
		frappe.throw(_("No unseen prompts remain. Reset this group's history or choose another pack."))
	return random.sample(remaining, min(count, len(remaining)))


def prepare(key, config, requested=None, previous=None, reset=False):
	scope, ids = content_source(key, config)
	if scope is None:
		return None
	if not ids:
		frappe.throw(_("That pack has no prompts."))
	previous = previous or {}
	if previous and previous.get("scope") != scope and not reset:
		frappe.throw(_("The pack language changed. Start a new sequence for this pack."))
	count = previous.get("requested") if previous else None
	count = count or count_value(requested, len(ids), 3 if key == "common-ground" else 10)
	used = sorted(set(previous.get("used", []) + previous.get("seen", []))) if previous and not reset else []
	selected = draw(ids, count, used)
	return {
		"scope": scope,
		"requested": count,
		"selected": selected,
		"used": used,
		"seen": [],
		"available": len(ids),
	}


def batch_of(doc):
	return frappe.parse_json(doc.get("play_batch")) or {}


def selected_ids(ctx):
	return ctx.configuration.get("_selected_ids")


def note_seen(doc, ids):
	if not ids:
		return
	# Serialize with replay and other observation updates. No Redis-only history.
	value = frappe.db.get_value(doc.doctype, doc.name, "play_batch", for_update=True)
	batch = frappe.parse_json(value) or {}
	if not batch:
		return
	seen = sorted(set(batch.get("seen", [])) | (set(ids) & set(batch["selected"])))
	if seen != batch.get("seen"):
		batch["seen"] = seen
		frappe.db.set_value(doc.doctype, doc.name, "play_batch", frappe.as_json(batch), update_modified=False)


def observe_transition(doc, state):
	ms = state.get("module_state") or {}
	key = doc.game_key
	ids = []
	if key == "cuecast" and state.get("phase") == "turn_open":
		from quizzly.games.engine import accepted_actions

		pos = ms.get("turn_start_pos", 0) + len(accepted_actions(doc.name, ms.get("round_index")))
		ids = ms.get("prompt_ids", [])[: pos + 1]
	elif key == "common-ground":
		batch = batch_of(frappe.get_doc(doc.doctype, doc.name))
		ids = batch.get("selected", [])[: ms.get("position", 0) + 1]
	elif key == "crowd-compass":
		ids = [ms.get("current", {}).get("content_id")]
	elif key == "doodle-dash":
		ids = ms.get("prompt_ids", [])[: ms.get("position", 0)]
	elif ms.get("item"):
		ids = [ms["item"]]
	note_seen(doc, [i for i in ids if i is not None])


def summary(doc):
	batch = batch_of(doc)
	if not batch:
		return None
	key = "quiz" if doc.doctype == "QZ Session" else doc.game_key
	config = {"pack": doc.quiz} if key == "quiz" else frappe.parse_json(doc.configuration)
	scope, ids = content_source(key, config)
	used = set(batch.get("used", []) + batch.get("seen", []))
	remaining = len(set(ids) - used)
	return {
		"requested": batch["requested"],
		"selected": len(batch["selected"]),
		"available": len(ids),
		"seen": len(used & set(ids)),
		"remaining": remaining,
		"next_count": min(batch["requested"], remaining),
		"scope_changed": scope != batch["scope"],
	}


def protect_session(doc, method=None):
	from quizzly.publishing import check_published

	if doc.is_new():
		check_published("quiz" if doc.doctype == "QZ Session" else doc.game_key)
	else:
		old = doc.get_doc_before_save()
		if old and any(
			doc.get(k) != old.get(k)
			for k in (
				"play_batch",
				"next_session",
				"host",
				"gatherplay_access",
				"configuration",
				"quiz",
				"game_key",
			)
		):
			frappe.throw(
				_("Session identity and replay history are managed by the game server."),
				frappe.PermissionError,
			)


def locked_doc(doctype, name):
	# A plain reload would reuse a repeatable-read snapshot opened before the lock.
	# Read the successor pointer from the current locked row, including on retries.
	row = frappe.db.get_value(doctype, name, "*", as_dict=True, for_update=True)
	if not row:
		frappe.throw(_("This session no longer exists."), frappe.DoesNotExistError)
	return frappe.get_doc({"doctype": doctype, **row})


@frappe.whitelist(methods=["POST"])
def replay(session: str, quiz: bool = False, reset: bool = False) -> dict:
	from quizzly.publishing import check_published

	dt = "QZ Session" if int(quiz) else "GP Session"
	reset = bool(int(reset))
	source = access.authorize_host(frappe.get_doc(dt, session))
	key = "quiz" if int(quiz) else source.game_key
	# The response is retryable even after a format has since been unpublished.
	with frappe.cache.lock(f"gp:replay:{dt}:{session}", timeout=60, blocking_timeout=10):
		source = access.authorize_host(locked_doc(dt, session))
		if source.next_session:
			next_doc = access.authorize_host(locked_doc(dt, source.next_session))
			return {"session": next_doc.name, "game_pin": next_doc.game_pin}
		if source.status != "Ended":
			frappe.throw(_("Finish this room before starting another batch."))
		check_published(key)
		config = {"pack": source.quiz} if int(quiz) else frappe.parse_json(source.configuration)
		previous = batch_of(source)
		scope, _ids = content_source(key, config)
		if not previous and scope is not None:
			# Legacy rooms lack a reliable observation ledger; never promise no repeats.
			if not reset:
				frappe.throw(_("This older room has no replay history. Reset to start a tracked sequence."))
		batch = prepare(key, config, previous=previous, reset=reset)
		if int(quiz):
			from quizzly import api as quiz_api
			from quizzly.api import create_session

			created = (
				access.create_guest_session(quiz_api, {"quiz": source.quiz})
				if access.is_guest()
				else create_session(source.quiz)
			)
		else:
			from quizzly.games import api as game_api
			from quizzly.games.api import create_session

			created = (
				access.create_guest_session(game_api, {"game_key": key, "configuration": config})
				if access.is_guest()
				else create_session(key, config)
			)
		next_doc = frappe.get_doc(dt, created["session"])
		if dt == "QZ Session":
			frappe.db.set_value(
				dt,
				next_doc.name,
				{
					"auto_advance": source.auto_advance,
					"randomize_answer_order": source.randomize_answer_order,
				},
			)
		if batch:
			frappe.db.set_value(dt, next_doc.name, "play_batch", frappe.as_json(batch))
			if dt == "GP Session":
				config = frappe.parse_json(next_doc.configuration)
				if key != "cuecast":
					config["rounds"] = len(batch["selected"])
				frappe.db.set_value(dt, next_doc.name, "configuration", frappe.as_json(config))
		copy_participants(source, next_doc)
		frappe.db.set_value(dt, source.name, "next_session", next_doc.name)
		frappe.db.commit()
		return created


def copy_participants(source, target):
	dt = "QZ Participant" if source.doctype == "QZ Session" else "GP Participant"
	filters = {
		"session": source.name,
		**({"kicked": 0} if dt == "QZ Participant" else {"status": ["!=", "Kicked"]}),
	}
	for row in frappe.get_all(
		dt, filters=filters, fields=["nickname", "avatar", "token_hash"], order_by="joined_at asc"
	):
		participant = frappe.get_doc(
			{
				"doctype": dt,
				"session": target.name,
				"nickname": row.nickname,
				"avatar": row.avatar,
				"token_hash": row.token_hash,
				"joined_at": frappe.utils.now_datetime(),
			}
		).insert(ignore_permissions=True)
		if dt == "GP Participant":
			from quizzly.games.board_session import assign_joiner

			assign_joiner(target, participant)


def continuation(doc, participant=None):
	if not doc.next_session:
		return None
	next_doc = frappe.get_doc(doc.doctype, doc.next_session)
	result = {
		"session": next_doc.name,
		"game_pin": next_doc.game_pin,
		"game_key": next_doc.get("game_key") or "quiz",
	}
	if participant:
		name = frappe.db.get_value(
			participant.doctype, {"session": next_doc.name, "token_hash": participant.token_hash}, "name"
		)
		if not name:
			return None
		result["participant"] = name
	return result
