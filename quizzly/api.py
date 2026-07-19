import hashlib
import secrets
import time

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime, strip_html_tags

from quizzly import engine
from quizzly.engine import publish_session_event

NICKNAME_MAX_LENGTH = 20

# Host APIs


@frappe.whitelist()
def create_session(quiz: str) -> dict:
	quiz_doc = frappe.get_doc("QZ Quiz", quiz)
	quiz_doc.check_permission("read")
	session = frappe.get_doc(
		{
			"doctype": "QZ Session",
			"quiz": quiz_doc.name,
			"host": frappe.session.user,
			"game_pin": generate_game_pin(),
			"status": "Lobby",
		}
	).insert()
	return {"session": session.name, "game_pin": session.game_pin}


@frappe.whitelist()
def lock_lobby(session: str) -> dict:
	return set_lobby_locked(session, True)


@frappe.whitelist()
def unlock_lobby(session: str) -> dict:
	return set_lobby_locked(session, False)


@frappe.whitelist()
def kick_participant(session: str, participant: str) -> None:
	session_doc = get_host_session(session)
	participant_doc = frappe.get_doc("QZ Participant", participant)
	if participant_doc.session != session_doc.name:
		frappe.throw(_("Participant does not belong to this session"))
	participant_doc.kicked = 1
	participant_doc.save(ignore_permissions=True)
	publish_session_event(session_doc, {"type": "kicked", "participant": participant_doc.name})
	publish_lobby_update(session_doc)


@frappe.whitelist()
def get_lobby(session: str) -> dict:
	session_doc = get_host_session(session)
	return get_lobby_state(session_doc)


@frappe.whitelist()
def start_session(session: str) -> dict:
	session_doc = get_host_session(session)
	if session_doc.status != "Lobby":
		frappe.throw(_("Session has already started"))
	if not frappe.db.exists("QZ Participant", {"session": session_doc.name, "kicked": 0}):
		frappe.throw(_("No participants have joined yet"))
	session_doc.status = "Active"
	session_doc.started_at = now_datetime()
	session_doc.save()
	engine.enqueue_game_loop(session_doc)
	publish_session_event(session_doc, {"type": "session_started"})
	return {"ok": True}


@frappe.whitelist()
def next_question(session: str) -> dict:
	engine.set_control(get_host_session(session).name, "advance")
	return {"ok": True}


@frappe.whitelist()
def skip_question(session: str) -> dict:
	engine.set_control(get_host_session(session).name, "skip")
	return {"ok": True}


@frappe.whitelist()
def end_session(session: str) -> dict:
	session_doc = get_host_session(session)
	if session_doc.status == "Lobby":
		session_doc.status = "Cancelled"
		session_doc.ended_at = now_datetime()
		session_doc.save()
		publish_session_event(session_doc, {"type": "session_ended"})
	elif session_doc.status == "Active":
		engine.set_control(session_doc.name, "end")
	return {"ok": True}


# Guest APIs


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def join_session(pin: str, nickname: str) -> dict:
	session = get_session_by_pin(pin)
	if session.status != "Lobby":
		frappe.throw(_("Game has already started"))
	if session.lobby_locked:
		frappe.throw(_("Lobby is locked"))

	token = secrets.token_hex(32)
	participant = frappe.get_doc(
		{
			"doctype": "QZ Participant",
			"session": session.name,
			"nickname": strip_html_tags(nickname or "")[:NICKNAME_MAX_LENGTH],
			"token_hash": hash_token(token),
			"joined_at": now_datetime(),
		}
	).insert(ignore_permissions=True)
	publish_lobby_update(session)
	return {
		"participant_token": token,
		"participant": participant.name,
		"nickname": participant.nickname,
		"session": session.name,
		"game_pin": session.game_pin,
		**get_lobby_state(session),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=30, seconds=60)
def submit_answer(pin: str, token: str, question_row: str, selected_option: str) -> dict:
	received_at = time.time()
	session = get_session_by_pin(pin)
	if session.status != "Active":
		frappe.throw(_("Game is not active"))
	participant = get_participant_by_token(session, token)

	state = engine.get_state(session.name)
	if not state or state.get("status") != "question" or state.get("question_row") != question_row:
		frappe.throw(_("This question is not open"))
	if received_at > state["deadline_ts"] + engine.GRACE_SECONDS:
		frappe.throw(_("Too late, the question is closed"))
	if str(selected_option) not in ("1", "2", "3", "4"):
		frappe.throw(_("Invalid option"))

	if not engine.mark_answered(
		session.name, question_row, participant.name, ttl=state["window_ms"] / 1000 + 300
	):
		frappe.throw(_("Already answered"))
	try:
		frappe.get_doc(
			{
				"doctype": "QZ Answer",
				"session": session.name,
				"participant": participant.name,
				"question_row": question_row,
				"selected_option": str(selected_option),
				"response_ms": int((received_at - state["opened_at"]) * 1000),
			}
		).insert(ignore_permissions=True)
	except frappe.UniqueValidationError:
		frappe.throw(_("Already answered"))
	publish_session_event(
		session,
		{
			"type": "answer_count",
			"question_row": question_row,
			"count": engine.answered_count(session.name, question_row),
		},
	)
	return {"ok": True}


@frappe.whitelist(allow_guest=True)
@rate_limit(key="token", limit=60, seconds=60)
def get_state(pin: str, token: str) -> dict:
	session = get_session_by_pin(pin)
	participant = get_participant_by_token(session, token)
	result = {
		"status": session.status,
		"nickname": participant.nickname,
		"score": participant.score,
		"streak": participant.streak,
	}
	if session.status == "Lobby":
		return {**result, **get_lobby_state(session)}

	state = engine.get_state(session.name)
	if not state:
		return result
	question = get_question_row(session, state["question_row"])
	result.update(
		{
			"phase": state["status"],
			"q_index": state["q_index"],
			"total": state["total"],
			"deadline_ts": state["deadline_ts"],
			"remaining_seconds": max(0.0, state["deadline_ts"] - time.time()),
			"answered": engine.has_answered(session.name, state["question_row"], participant.name),
			"question": engine.question_payload(
				question, state["q_index"], state["total"], state["deadline_ts"]
			),
		}
	)
	return result


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def leave_session(pin: str, token: str) -> None:
	session = get_session_by_pin(pin)
	participant = get_participant_by_token(session, token)
	# ponytail: leave only matters in the lobby; mid-game the row must survive for scores
	if session.status == "Lobby":
		frappe.delete_doc("QZ Participant", participant.name, ignore_permissions=True, force=True)
		publish_lobby_update(session)


# Helpers


def get_host_session(session: str) -> "frappe.model.document.Document":
	doc = frappe.get_doc("QZ Session", session)
	if doc.host != frappe.session.user:
		frappe.throw(_("You are not the host of this session"), frappe.PermissionError)
	return doc


def get_session_by_pin(pin: str) -> "frappe.model.document.Document":
	pin = (pin or "").strip()
	name = pin and frappe.db.get_value("QZ Session", {"game_pin": pin, "status": ("in", ("Lobby", "Active"))})
	if not name:
		frappe.throw(_("Invalid game PIN"), frappe.DoesNotExistError)
	return frappe.get_doc("QZ Session", name)


def get_participant_by_token(
	session: "frappe.model.document.Document", token: str
) -> "frappe.model.document.Document":
	name = frappe.db.get_value(
		"QZ Participant",
		{"session": session.name, "token_hash": hash_token(token or ""), "kicked": 0},
	)
	if not name:
		frappe.throw(_("Not a participant of this session"), frappe.PermissionError)
	return frappe.get_doc("QZ Participant", name)


def get_lobby_state(session: "frappe.model.document.Document") -> dict:
	participants = frappe.get_all(
		"QZ Participant",
		filters={"session": session.name, "kicked": 0},
		fields=["name", "nickname"],
		order_by="joined_at asc",
	)
	return {
		"status": session.status,
		"lobby_locked": session.lobby_locked,
		"participants": participants,
	}


def set_lobby_locked(session: str, locked: bool) -> dict:
	doc = get_host_session(session)
	doc.lobby_locked = int(locked)
	doc.save()
	publish_lobby_update(doc)
	return get_lobby_state(doc)


def publish_lobby_update(session: "frappe.model.document.Document") -> None:
	publish_session_event(session, {"type": "lobby_update", **get_lobby_state(session)})


def get_question_row(
	session: "frappe.model.document.Document", question_row: str
) -> "frappe.model.document.Document":
	for question in engine.get_quiz_questions(session):
		if question.name == question_row:
			return question
	frappe.throw(_("Question not found"))


def hash_token(token: str) -> str:
	return hashlib.sha256(token.encode()).hexdigest()


def generate_game_pin() -> str:
	# ponytail: pins stay unique forever (DB unique column); revisit if sessions ever near 1M
	for _attempt in range(20):
		pin = f"{secrets.randbelow(1_000_000):06d}"
		if not frappe.db.exists("QZ Session", {"game_pin": pin}):
			return pin
	frappe.throw(_("Could not allocate a game PIN, please retry"))
