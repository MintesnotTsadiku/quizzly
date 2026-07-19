import hashlib
import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime, strip_html_tags

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
	name = pin and frappe.db.get_value(
		"QZ Session", {"game_pin": pin, "status": ("in", ("Lobby", "Active"))}
	)
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


def publish_session_event(session: "frappe.model.document.Document", message: dict) -> None:
	room = f"qz_session_{session.game_pin}"
	frappe.publish_realtime(event=room, message=message, room=room, after_commit=True)


def hash_token(token: str) -> str:
	return hashlib.sha256(token.encode()).hexdigest()


def generate_game_pin() -> str:
	# ponytail: pins stay unique forever (DB unique column); revisit if sessions ever near 1M
	for _attempt in range(20):
		pin = f"{secrets.randbelow(1_000_000):06d}"
		if not frappe.db.exists("QZ Session", {"game_pin": pin}):
			return pin
	frappe.throw(_("Could not allocate a game PIN, please retry"))
