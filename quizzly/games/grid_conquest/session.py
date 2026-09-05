"""Locked, durable moves for a human-paced board. No background timer owns it."""

import json

import frappe
from frappe import _


def is_board(doc):
	return (
		doc.game_key == "grid-conquest"
		and (frappe.parse_json(doc.configuration) or {}).get("rules_version") == 2
	)


def checkpoint(doc, state):
	from quizzly.games import engine

	row = engine.get_round_name(doc.name, state["module_state"]["round_index"])
	if row:
		value = frappe.parse_json(frappe.db.get_value("GP Round", row, "resolution")) or {}
		value["grid_snapshot"] = state
		frappe.db.set_value("GP Round", row, "resolution", json.dumps(value), update_modified=False)


def restore(session, *, for_update=False):
	row = frappe.db.get_value("GP Session", session, ["game_key", "configuration", "status"], as_dict=True)
	if not row or row.status != "Active" or not is_board(row):
		return None
	# Locking reads see the latest committed revision even under MariaDB's
	# repeatable-read isolation, after a request waited behind another move.
	resolution = frappe.db.get_value(
		"GP Round", {"session": session}, "resolution", order_by="round_index desc", for_update=for_update
	)
	state = (frappe.parse_json(resolution) or {}).get("grid_snapshot")
	# Return the durable snapshot without writing the cache: concurrent readers must
	# never overwrite a newer move with a stale recovered version.
	return state


def command(doc, action, payload, participant=None):
	from quizzly.games import engine, get_game_module

	with frappe.cache.lock(f"gp:board:{doc.name}", timeout=30):
		# Row lock also serializes commits if a request outlives the Redis lock lease.
		status = frappe.db.get_value("GP Session", doc.name, "status", for_update=True)
		if status != "Active":
			frappe.throw(_("Game is not active"))
		state = restore(doc.name, for_update=True)
		if not state:
			frappe.throw(_("This room has expired. Start a new game."))
		if payload.get("revision") != state["version"]:
			frappe.throw(_("The board changed. Check the latest turn and try again."))
		module = get_game_module(doc.game_key)
		ctx = engine.context_for(doc)
		if participant:
			# A kicked token cannot race through a previously successful authentication.
			if frappe.db.get_value("GP Participant", participant.name, "status", for_update=True) == "Kicked":
				frappe.throw(_("You are no longer in this room."), frappe.PermissionError)
		if action == "place_mark":
			transition = module.move(
				ctx,
				state,
				payload.get("cell"),
				participant=participant.name if participant else None,
				host=not participant,
			)
		elif participant:
			frappe.throw(_("Unknown game action"))
		elif action == "next":
			if state.get("paused"):
				frappe.throw(_("Resume the game first."))
			transition = module.next_board(ctx, state)
		elif action in ("pause", "resume"):
			state = {**state, "paused": action == "pause"}
			transition = module.transition(ctx, state["module_state"])
		elif action == "take_over":
			if state["phase"] != "grid_turn":
				frappe.throw(_("This board is finished."))
			ms = dict(state["module_state"])
			ms["host_turn"] = True
			transition = module.transition(ctx, ms)
		elif action == "pass_controller":
			if state["phase"] != "grid_turn":
				frappe.throw(_("This board is finished."))
			ms = dict(state["module_state"])
			ms["moves"] = dict(ms["moves"])
			ms["moves"][ms["turn"]] += 1
			module.select_controller(ctx, ms)
			transition = module.transition(ctx, ms)
		elif action == "end":
			engine.finish_session(doc)
			return {"ok": True}
		else:
			frappe.throw(_("Unknown host command"))
		if action == "place_mark" and participant:
			engine.record_action(
				doc,
				engine.get_round_name(doc.name, state["module_state"]["round_index"]),
				participant,
				action,
				{"cell": payload.get("cell"), "revision": state["version"]},
				f"board-move:{state['version']}",
			)
		engine.apply_transition(doc, state, transition)
		frappe.db.commit()
		return {"ok": True}


def assign_joiner(doc, participant):
	if not is_board(doc) or doc.status != "Active":
		return
	with frappe.cache.lock(f"gp:board:{doc.name}", timeout=30):
		teams = frappe.get_all(
			"GP Team", filters={"session": doc.name}, fields=["name", "seed"], order_by="seed asc"
		)
		if len(teams) != 2:
			return
		team = min(
			teams,
			key=lambda t: frappe.db.count(
				"GP Participant", {"session": doc.name, "team": t.name, "status": ("!=", "Kicked")}
			),
		)
		frappe.db.set_value("GP Participant", participant.name, "team", team.name)
		frappe.get_doc(
			{
				"doctype": "GP Team Membership",
				"session": doc.name,
				"team": team.name,
				"participant": participant.name,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
