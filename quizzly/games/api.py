"""Whitelisted APIs for GatherPlay sessions.

Same safe division as the quiz: socket.io pushes public events, every client action is
an HTTP call here. Guests act with their participant token; hosts must own the session.
"""

from __future__ import annotations

import secrets
import time

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime, strip_html_tags

from quizzly.api import generate_game_pin, hash_token
from quizzly.games import GameContext, get_game_module
from quizzly.games import engine as gpe
from quizzly.games.round_games.game import PROFILES as ROUND_GAME_PROFILES
from quizzly.profanity import is_profane

NICKNAME_MAX_LENGTH = 20


# --- discovery ---------------------------------------------------------------


# The catalog is browsable without an account (product spec §5).
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True)
def list_games() -> list[dict]:
	"""The /play catalog: backend manifests are authoritative."""
	from quizzly.games import manifests

	return [
		{
			"key": m.key,
			"title": m.title,
			"summary": m.summary,
			"min_players": m.min_players,
			"max_players": m.max_players,
			"recommended_players": m.recommended_players,
			"typical_minutes": m.typical_minutes,
			"interaction_tags": list(m.interaction_tags),
			"status": m.status,
			"frontend_key": m.frontend_key,
		}
		for m in sorted(manifests(), key=lambda m: m.title)
	]


CONTENT_PREVIEWS = {
	"cuecast": {
		"pack_doctype": "GP Cue Deck",
		"prompt_doctype": "GP Cue Prompt",
		"metadata_field": "mode",
		"choice_fields": (),
	},
	"crowd-compass": {
		"pack_doctype": "GP Crowd Pack",
		"prompt_doctype": "GP Crowd Prompt",
		"metadata_field": "ranked",
		"choice_fields": ("choice_1", "choice_2", "choice_3", "choice_4"),
		"text_field": "prompt_text",
	},
	"doodle-dash": {
		"pack_doctype": "GP Draw Pack",
		"prompt_doctype": "GP Draw Prompt",
		"metadata_field": "description",
		"choice_fields": (),
	},
	"quiz": {
		"pack_doctype": "QZ Quiz",
		"prompt_doctype": "QZ Question",
		"metadata_field": "default_time_limit",
		"choice_fields": ("option_1", "option_2", "option_3", "option_4"),
		"text_field": "question_text",
	},
}

ROUND_GAME_KEYS = set(ROUND_GAME_PROFILES)
for _game_key in ROUND_GAME_KEYS:
	CONTENT_PREVIEWS[_game_key] = {
		"pack_doctype": "GP Game Pack",
		"prompt_doctype": "GP Game Item",
		"metadata_field": "description",
		"choice_fields": (),
	}


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True)
def list_public_decks(game_key: str | None = None) -> list[dict]:
	"""Demo packs are marketing content: browsable by guests, playable by hosts."""
	preview = CONTENT_PREVIEWS.get(game_key or "")
	if not preview:
		return []
	pack_doctype = preview["pack_doctype"]
	prompt_doctype = preview["prompt_doctype"]
	choice_fields = preview["choice_fields"]
	text_field = preview.get("text_field", "prompt_text")
	filters = {"is_demo": 1}
	if pack_doctype == "GP Game Pack":
		filters["game_key"] = game_key
	roster = frappe.get_all(
		pack_doctype,
		filters=filters,
		fields=["name", "title", "demo_key", preview["metadata_field"]],
		order_by="title asc",
	)
	for pack in roster:
		prompt_fields = [text_field, *choice_fields]
		rows = frappe.get_all(
			prompt_doctype,
			filters={"parent": pack.name, "parenttype": pack_doctype},
			fields=prompt_fields,
			order_by="idx asc",
		)
		pack.prompt_count = len(rows)
		pack.prompts = [
			{
				"text": strip_html_tags(row.get(text_field) or "").strip(),
				"choices": [
					strip_html_tags(row.get(field) or "").strip() for field in choice_fields if row.get(field)
				],
			}
			for row in rows
		]
	return roster


# --- host --------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def create_session(game_key: str, configuration: dict | str | None = None) -> dict:
	configuration = as_dict(configuration)
	module = get_game_module(game_key)
	ctx = GameContext(session="", pin="", game_key=game_key, configuration=configuration)
	normalized = module.validate_configuration(ctx, configuration)
	normalized["auto_progress"] = bool(int(configuration.get("auto_progress", 1)))
	session_doc = frappe.get_doc(
		{
			"doctype": "GP Session",
			"game_key": game_key,
			"host": frappe.session.user,
			"game_pin": generate_game_pin(),
			"status": "Lobby",
			"configuration": normalized,
		}
	).insert()
	return {"session": session_doc.name, "game_pin": session_doc.game_pin}


@frappe.whitelist()
def get_host_state(session: str | None = None) -> dict:
	session_doc = get_host_session(session) if session else get_live_host_session()
	if not session_doc or session_doc.status == "Cancelled":
		return {}
	if gpe.is_abandoned(session_doc):
		gpe.finish_session(session_doc)
		session_doc.reload()
	result = {
		"session": session_doc.name,
		"game_pin": session_doc.game_pin,
		"game_key": session_doc.game_key,
		"title": get_game_module(session_doc.game_key).manifest.title,
		"configuration": frappe.parse_json(session_doc.get("configuration")) or {},
		**lobby_state(session_doc),
	}
	if session_doc.status == "Ended":
		result["podium"] = final_leaderboard(session_doc.name)
		return result
	if session_doc.status != "Active":
		return result

	state = gpe.get_state(session_doc.name)
	if not state:
		result["podium"] = final_leaderboard(session_doc.name)
		return result
	module = get_game_module(session_doc.game_key)
	result.update(
		{
			"phase": state["phase"],
			"state_version": state["version"],
			"remaining_seconds": max(0.0, state["deadline_ts"] - time.time()),
			"view": {
				**module.serialize_host_state(gpe.context_for(session_doc), state),
				"paused": bool(state.get("paused")),
				"can_previous": bool(state.get("presentation_history")),
				"presentation_replay": bool(state.get("presentation_replay")),
			},
		}
	)
	return result


@frappe.whitelist()
def start_session(session: str) -> dict:
	session_doc = get_host_session(session)
	if session_doc.status != "Lobby":
		frappe.throw(_("Session has already started"))
	participants = lobby_participants(session_doc.name)
	if not participants:
		frappe.throw(_("No participants have joined yet"))
	module = get_game_module(session_doc.game_key)
	session_doc.status = "Active"
	session_doc.started_at = now_datetime()
	session_doc.save()
	ctx = gpe.context_for(session_doc)
	first = module.start_game(ctx, participants)
	publish_lobby_update(session_doc)
	gpe.enqueue_game_loop(session_doc, first)
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def host_command(session: str, command: str, payload: dict | str | None = None) -> dict:
	"""Lobby commands mutate and republish; live commands ride the control flag."""
	payload = as_dict(payload)
	session_doc = get_host_session(session)
	if (
		command
		not in {
			"previous",
			"next",
			"pause",
			"resume",
			"skip_turn",
			"end",
			"reassign_performer",
			"push_prompt",
			"void_prompt",
		}
		and session_doc.status != "Lobby"
	):
		frappe.throw(_("Unknown host command"))
	if command == "end":
		return end_session(session)
	if session_doc.status == "Lobby":
		return apply_lobby_command(session_doc, command, payload)
	gpe.set_control(session_doc.name, {"command": command, **payload})
	return {"ok": True}


LOBBY_COMMANDS = {"balance_teams", "rename_team", "recolor_team"}


def apply_lobby_command(session_doc, command: str, payload: dict) -> dict:
	if command not in LOBBY_COMMANDS:
		frappe.throw(_("Command not available in the lobby"))
	if command == "balance_teams":
		count = int(payload.get("count") or 2)
		participants = lobby_participants(session_doc.name)
		if len(participants) < count:
			frappe.throw(_("Not enough players for {0} teams").format(count))
		gpe.create_teams(session_doc.name, participants, count)
	elif command == "rename_team":
		name = strip_html_tags(str(payload.get("team_name") or "")).strip()[:30]
		if not name:
			frappe.throw(_("Team name cannot be empty"))
		check_team_in_session(session_doc, payload.get("team"))
		frappe.db.set_value("GP Team", payload["team"], "team_name", name)
	else:
		color = str(payload.get("color") or "")
		if color not in gpe.TEAM_COLORS:
			frappe.throw(_("Unknown color"))
		check_team_in_session(session_doc, payload.get("team"))
		frappe.db.set_value("GP Team", payload["team"], "color", color)
	publish_lobby_update(session_doc)
	return {"ok": True}


def check_team_in_session(session_doc, team: str | None) -> None:
	if not team or frappe.db.get_value("GP Team", team, "session") != session_doc.name:
		frappe.throw(_("Team does not belong to this session"), frappe.PermissionError)


@frappe.whitelist()
def lock_lobby(session: str) -> dict:
	return set_lobby_locked(session, True)


@frappe.whitelist()
def unlock_lobby(session: str) -> dict:
	return set_lobby_locked(session, False)


@frappe.whitelist()
def kick_participant(session: str, participant: str) -> None:
	session_doc = get_host_session(session)
	if frappe.db.get_value("GP Participant", participant, "session") != session_doc.name:
		frappe.throw(_("Participant does not belong to this session"))
	frappe.db.set_value("GP Participant", participant, "status", "Kicked")
	state = gpe.get_state(session_doc.name) or {}
	gpe.publish_session_event(
		session_doc, state, "platform.participant_removed", {"participant": participant}
	)
	publish_lobby_update(session_doc)


@frappe.whitelist()
def end_session(session: str) -> dict:
	session_doc = get_host_session(session)
	if session_doc.status == "Lobby":
		session_doc.status = "Cancelled"
		session_doc.ended_at = now_datetime()
		session_doc.save()
		gpe.publish_session_event(session_doc, {}, "platform.session_ended", {"cancelled": True})
	elif session_doc.status == "Active":
		gpe.end_active_session(session_doc)
	return {"ok": True}


# --- guests ------------------------------------------------------------------


# Guests join by design (no login); rate-limited, PIN-gated, and input is sanitized below.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def join_session(pin: str, nickname: str, avatar: str | None = None) -> dict:
	session_doc = get_session_by_pin(pin)
	if session_doc.status != "Lobby":
		frappe.throw(_("Game has already started"))
	if session_doc.lobby_locked:
		frappe.throw(_("Lobby is locked"))

	nickname = strip_html_tags(nickname or "").strip()[:NICKNAME_MAX_LENGTH]
	if is_profane(nickname):
		frappe.throw(_("Pick a nickname everyone can see on the big screen"))
	if frappe.db.exists(
		"GP Participant", {"session": session_doc.name, "nickname": nickname, "status": ("!=", "Kicked")}
	):
		frappe.throw(_("That nickname is taken, pick another"), frappe.DuplicateEntryError)

	token = secrets.token_hex(32)
	participant = frappe.get_doc(
		{
			"doctype": "GP Participant",
			"session": session_doc.name,
			"nickname": nickname,
			"avatar": avatar,
			"token_hash": hash_token(token),
			"joined_at": now_datetime(),
		}
	).insert(ignore_permissions=True)
	publish_lobby_update(session_doc)
	return {
		"participant_token": token,
		"participant": participant.name,
		"nickname": participant.nickname,
		"avatar": participant.avatar,
		"session": session_doc.name,
		"game_pin": session_doc.game_pin,
		"game_key": session_doc.game_key,
		**lobby_state(session_doc),
	}


# Players are guests by design; the participant token gates every read below.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True)
@rate_limit(key="token", limit=60, seconds=60)
def get_player_state(pin: str, token: str) -> dict:
	session_doc = get_session_by_pin(pin)
	participant = get_participant_by_token(session_doc, token)
	result = {
		"status": session_doc.status,
		"nickname": participant.nickname,
		"avatar": participant.avatar,
		"score": participant.score,
		"team": team_view(participant.team),
	}
	if session_doc.status == "Lobby":
		return {**result, **lobby_state(session_doc)}
	if session_doc.status == "Ended":
		return {
			**result,
			"podium": final_leaderboard(session_doc.name),
			"rank": participant.rank,
		}

	state = gpe.get_state(session_doc.name)
	if not state:
		return result
	module = get_game_module(session_doc.game_key)
	view = module.serialize_player_state(gpe.context_for(session_doc), state, participant_view(participant))
	return {
		**result,
		"phase": state["phase"],
		"state_version": state["version"],
		"remaining_seconds": max(0.0, state["deadline_ts"] - time.time()),
		"view": view,
	}


# The projector knows the PIN and nothing else, so this snapshot stays public-safe.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=60)
def get_public_state(pin: str) -> dict:
	session_doc = get_session_by_pin(pin, graceful=True)
	if not session_doc:
		# a projector polling a stale or wrong pin degrades quietly, not with 404 spam
		return {"status": "Unknown"}
	result = {
		"status": session_doc.status,
		"game_key": session_doc.game_key,
		"title": get_game_module(session_doc.game_key).manifest.title,
	}
	if session_doc.status == "Ended":
		return {**result, "podium": final_leaderboard(session_doc.name)}
	if session_doc.status != "Active":
		return {**result, **public_lobby_state(session_doc)}

	state = gpe.get_state(session_doc.name)
	if not state:
		return result
	module = get_game_module(session_doc.game_key)
	return {
		**result,
		"phase": state["phase"],
		"state_version": state["version"],
		"remaining_seconds": max(0.0, state["deadline_ts"] - time.time()),
		"view": module.serialize_public_state(gpe.context_for(session_doc), state),
	}


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=60, seconds=60)
def submit_action(
	pin: str, token: str, action_type: str, idempotency_key: str, payload: dict | str | None = None
) -> dict:
	session_doc = get_session_by_pin(pin)
	if session_doc.status != "Active":
		frappe.throw(_("Game is not active"))
	participant = get_participant_by_token(session_doc, token)
	idempotency_key = str(idempotency_key or "").strip()[:64]
	if not idempotency_key:
		frappe.throw(_("Missing idempotency key"))

	state = gpe.get_state(session_doc.name)
	if not state:
		frappe.throw(_("Game is not active"))
	if state.get("paused"):
		frappe.throw(_("The host has paused this game"))
	module = get_game_module(session_doc.game_key)
	payload = as_dict(payload)
	decision = module.submit_action(
		gpe.context_for(session_doc), state, participant_view(participant), action_type, payload
	)
	if not decision.accepted:
		frappe.throw(_(decision.reason or "Action rejected"))

	replay_ttl = (state["deadline_ts"] - time.time()) + 300
	if not gpe.mark_acted(session_doc.name, idempotency_key, ttl=max(replay_ttl, 60)):
		return decision.result or {"ok": True}
	if session_doc.game_key == "doodle-dash" and action_type in {"stroke_batch", "clear_canvas"}:
		# High-frequency drawing data stays in Redis. Persisting every pointer batch
		# would turn one sketch into hundreds of SQL writes and slow large rooms.
		module.update_canvas(gpe.context_for(session_doc), state, action_type, payload or {})
		gpe.publish_session_event(
			session_doc,
			state,
			"doodle_dash.canvas_updated",
			module.serialize_public_state(gpe.context_for(session_doc), state),
		)
		return decision.result or {"ok": True}
	try:
		gpe.record_action(
			session_doc,
			gpe.get_round_name(session_doc.name, (state.get("module_state") or {}).get("round_index")),
			participant,
			action_type,
			payload or {},
			idempotency_key,
		)
	except frappe.UniqueValidationError:
		# the DB is the final word on replays that beat the Redis pre-check
		return decision.result or {"ok": True}
	return decision.result or {"ok": True}


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def leave_session(pin: str, token: str) -> None:
	session_doc = get_session_by_pin(pin)
	participant = get_participant_by_token(session_doc, token)
	# ponytail: leaving mid-game keeps the row for scores, exactly like the quiz
	if session_doc.status == "Lobby":
		frappe.delete_doc("GP Participant", participant.name, ignore_permissions=True, force=True)
		publish_lobby_update(session_doc)


# --- shared helpers ----------------------------------------------------------


def get_host_session(session: str):
	doc = frappe.get_doc("GP Session", session)
	if doc.host != frappe.session.user:
		frappe.throw(_("You are not the host of this session"), frappe.PermissionError)
	return doc


def as_dict(value: dict | str | None) -> dict:
	"""Normalize JSON object arguments sent by browser form transports."""
	if not value:
		return {}
	if isinstance(value, dict):
		return value
	parsed = frappe.parse_json(value)
	if not isinstance(parsed, dict):
		frappe.throw(_("Expected a JSON object"))
	return parsed


def get_live_host_session():
	names = frappe.get_all(
		"GP Session",
		filters={"host": frappe.session.user, "status": ("in", ("Lobby", "Active"))},
		pluck="name",
		order_by="creation desc",
	)
	for name in names:
		doc = frappe.get_doc("GP Session", name)
		if gpe.is_abandoned(doc):
			gpe.finish_session(doc)
			continue
		return doc
	return None


def get_session_by_pin(pin: str, graceful: bool = False):
	pin = (pin or "").strip()
	name = pin and frappe.db.get_value(
		"GP Session", {"game_pin": pin, "status": ("in", ("Lobby", "Active", "Ended"))}
	)
	if not name:
		if graceful:
			return None
		frappe.throw(_("Invalid game PIN"), frappe.DoesNotExistError)
	return frappe.get_doc("GP Session", name)


def get_participant_by_token(session_doc, token: str):
	name = frappe.db.get_value(
		"GP Participant",
		{"session": session_doc.name, "token_hash": hash_token(token or ""), "status": ("!=", "Kicked")},
	)
	if not name:
		frappe.throw(_("Not a participant of this session"), frappe.PermissionError)
	return frappe.get_doc("GP Participant", name)


def participant_view(participant) -> dict:
	team = team_view(participant.team)
	return {
		"name": participant.name,
		"nickname": participant.nickname,
		"avatar": participant.avatar,
		"role": participant.role,
		"team": team["name"] if team else None,
		"team_name": team["team_name"] if team else None,
		"team_color": team["color"] if team else None,
	}


def participant_view_by_name(session: str, participant: str) -> dict:
	row = frappe.db.get_value(
		"GP Participant", participant, ["name", "nickname", "avatar", "role", "team"], as_dict=True
	)
	team = team_view(row.team) if row else None
	return {
		"name": row.name,
		"nickname": row.nickname,
		"avatar": row.avatar,
		"role": row.role,
		"team": team["name"] if team else None,
		"team_name": team["team_name"] if team else None,
		"team_color": team["color"] if team else None,
	}


def team_view(team: str | None) -> dict | None:
	if not team:
		return None
	row = frappe.db.get_value("GP Team", team, ["name", "team_name", "color"], as_dict=True)
	return row and {"name": row.name, "team_name": row.team_name, "color": row.color}


def lobby_participants(session: str) -> list[dict]:
	rows = frappe.get_all(
		"GP Participant",
		filters={"session": session, "status": ("!=", "Kicked")},
		fields=["name", "nickname", "avatar", "team"],
		order_by="joined_at asc",
	)
	return [participant_view_by_name(session, row.name) for row in rows]


def team_roster(session: str) -> list[dict]:
	return frappe.get_all(
		"GP Team",
		filters={"session": session},
		fields=["name", "team_name", "color", "score"],
		order_by="seed asc",
	)


def lobby_state(session_doc) -> dict:
	return {
		"status": session_doc.status,
		"lobby_locked": session_doc.lobby_locked,
		"participants": lobby_participants(session_doc.name),
		"teams": team_roster(session_doc.name),
	}


def public_lobby_state(session_doc) -> dict:
	return {
		"participants": [
			{"nickname": p.nickname, "avatar": p.avatar}
			for p in frappe.get_all(
				"GP Participant",
				filters={"session": session_doc.name, "status": ("!=", "Kicked")},
				fields=["nickname", "avatar"],
				order_by="joined_at asc",
			)
		],
		"teams": team_roster(session_doc.name),
	}


def publish_lobby_update(session_doc) -> None:
	gpe.publish_session_event(session_doc, {}, "platform.lobby_updated", lobby_state(session_doc))


def final_leaderboard(session: str) -> list[dict]:
	teams = frappe.get_all(
		"GP Team",
		filters={"session": session},
		fields=["name", "team_name", "color", "score", "rank"],
		order_by="rank asc",
	)
	if teams and any(t.rank for t in teams):
		return [{"subject_type": "Team", **t} for t in teams]
	participants = frappe.get_all(
		"GP Participant",
		filters={"session": session, "status": ("!=", "Kicked")},
		fields=["name", "nickname", "avatar", "score", "rank"],
		order_by="rank asc",
	)
	# participant rows wear the platform's team-row shape so shells render one way
	from quizzly.games.engine import TEAM_COLORS

	return [
		{
			"subject_type": "Participant",
			"name": p.name,
			"team_name": p.nickname,
			"color": TEAM_COLORS[(p.rank or 1) % len(TEAM_COLORS) - 1],
			"avatar": p.avatar,
			"score": p.score,
			"rank": p.rank,
		}
		for p in participants
	]


def set_lobby_locked(session: str, locked: bool) -> dict:
	doc = get_host_session(session)
	frappe.db.set_value("GP Session", doc.name, "lobby_locked", int(locked))
	doc.reload()
	publish_lobby_update(doc)
	return lobby_state(doc)
