from __future__ import annotations

from collections import Counter, defaultdict

import frappe
from frappe.utils import get_datetime, now_datetime

from quizzly.games import manifests

ACTIVE_STATUSES = {"Lobby", "Active", "Paused"}


@frappe.whitelist(methods=["GET"])
def get_host_dashboard() -> dict:
	"""One permission-scoped view across legacy quiz and GatherPlay sessions."""
	user = frappe.session.user
	filters = {} if "System Manager" in frappe.get_roles(user) else {"host": user}
	quiz_sessions = _session_rows("QZ Session", filters)
	platform_sessions = _session_rows("GP Session", filters)

	quiz_names = [row.quiz for row in quiz_sessions if row.quiz]
	quiz_titles = (
		{
			row.name: row.title
			for row in frappe.get_all(
				"QZ Quiz",
				filters={"name": ["in", quiz_names]},
				fields=["name", "title"],
			)
		}
		if quiz_names
		else {}
	)
	game_titles = {manifest.key: manifest.title for manifest in manifests()}
	quiz_counts = _participant_counts("QZ Participant", [row.name for row in quiz_sessions])
	platform_counts = _participant_counts("GP Participant", [row.name for row in platform_sessions])

	sessions = [
		_format_session(
			row,
			"quiz",
			quiz_titles.get(row.quiz, "Quizzly"),
			quiz_counts[row.name],
			row.host == user,
		)
		for row in quiz_sessions
	]
	sessions.extend(
		_format_session(
			row,
			row.game_key,
			game_titles.get(row.game_key, row.game_key.replace("-", " ").title()),
			platform_counts[row.name],
			row.host == user,
		)
		for row in platform_sessions
	)
	sessions.sort(key=lambda row: row["created_at"], reverse=True)

	by_game = defaultdict(lambda: {"sessions": 0, "players": 0})
	for session in sessions:
		game = by_game[session["game_title"]]
		game["sessions"] += 1
		game["players"] += session["players"]

	completed = [session for session in sessions if session["status"] == "Ended"]
	return {
		"summary": {
			"total_sessions": len(sessions),
			"active_sessions": sum(session["status"] in ACTIVE_STATUSES for session in sessions),
			"completed_sessions": len(completed),
			"total_players": sum(session["players"] for session in sessions),
			"average_players": round(sum(session["players"] for session in completed) / len(completed), 1)
			if completed
			else 0,
		},
		"by_game": [
			{"game": game, **values}
			for game, values in sorted(by_game.items(), key=lambda item: (-item[1]["sessions"], item[0]))
		],
		"sessions": sessions,
	}


def _session_rows(doctype: str, filters: dict) -> list:
	fields = [
		"name",
		"host",
		"game_pin",
		"status",
		"creation",
		"started_at",
		"ended_at",
	]
	fields.append("quiz" if doctype == "QZ Session" else "game_key")
	return frappe.get_all(doctype, filters=filters, fields=fields)


def _participant_counts(doctype: str, sessions: list[str]) -> Counter:
	if not sessions:
		return Counter()
	return Counter(
		row.session
		for row in frappe.get_all(doctype, filters={"session": ["in", sessions]}, fields=["session"])
	)


def _format_session(row, game_key: str, game_title: str, players: int, can_open: bool) -> dict:
	start = get_datetime(row.started_at or row.creation)
	end = get_datetime(row.ended_at) if row.ended_at else now_datetime()
	return {
		"name": row.name,
		"game_key": game_key,
		"game_title": game_title,
		"pin": row.game_pin,
		"status": row.status,
		"is_active": row.status in ACTIVE_STATUSES,
		"can_open": can_open,
		"players": players,
		"created_at": row.creation,
		"started_at": row.started_at,
		"ended_at": row.ended_at,
		"duration_seconds": max(0, int((end - start).total_seconds())),
	}
