"""A real shared X/O board; legacy question sessions retain their original rules."""

import time
from copy import deepcopy

import frappe
from frappe import _

from quizzly.games import GameManifest, GameResult, Resolution, ScoreDelta, Transition
from quizzly.games.round_games.game import GridConquestGame as LegacyGrid

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))


def outcome(board):
	for line in LINES:
		if board[line[0]] and all(board[cell] == board[line[0]] for cell in line):
			return board[line[0]], list(line)
	return ("draw", []) if all(board) else (None, [])


def place(state, cell):
	"""Pure rule transition. Caller authenticates controller and locks session."""
	if type(cell) is not int or not 0 <= cell < 9:
		raise ValueError("Choose a square on the board.")
	if state.get("winner"):
		raise ValueError("This board is finished.")
	if state["board"][cell]:
		raise ValueError("That square is already taken.")
	next_state = deepcopy(state)
	mark = state["turn"]
	next_state["board"][cell] = mark
	next_state["last_cell"] = cell
	next_state["last_mark"] = mark
	next_state["moves"][mark] += 1
	next_state["winner"], next_state["winning_line"] = outcome(next_state["board"])
	if next_state["winner"] in ("X", "O"):
		next_state["wins"][mark] += 1
	next_state["turn"] = "O" if mark == "X" else "X"
	next_state["host_turn"] = False
	return next_state


class GridConquestGame(LegacyGrid):
	manifest = GameManifest(
		key="grid-conquest",
		title="Grid Conquest",
		version="2.0.0",
		summary="Two sides. One shared board. Take turns placing X and O to connect three.",
		min_players=2,
		max_players=None,
		recommended_players="2 sides · rotate players or share devices",
		typical_minutes=5,
		interaction_tags=("board", "teams", "strategy"),
		capabilities=("board", "teams", "reconnect"),
		host_commands=("next", "pass_controller", "pause", "resume"),
		frontend_key="grid-conquest",
	)

	def validate_configuration(self, ctx, configuration):
		mode = configuration.get("control_mode", "players")
		if mode not in ("players", "shared"):
			frappe.throw(_("Choose how to control the board."))
		return {"rules_version": 2, "control_mode": mode, "boards": 3, "auto_progress": False}

	def start_game(self, ctx, participants):
		if ctx.configuration.get("rules_version") != 2:
			return super().start_game(ctx, participants)
		from quizzly.games import engine

		if ctx.configuration["control_mode"] == "players" and len(participants) < 2:
			frappe.throw(_("Two playing devices are needed. Or choose one shared board."))
		if len(participants) >= 2:
			teams = engine.create_teams(ctx.session, participants, 2)
		else:
			teams = []
			for mark in ("X", "O"):
				doc = frappe.get_doc(
					{
						"doctype": "GP Team",
						"session": ctx.session,
						"team_name": mark,
						"color": "ember" if mark == "X" else "lagoon",
						"seed": len(teams) + 1,
					}
				).insert(ignore_permissions=True)
				teams.append({"name": doc.name, "team_name": mark, "color": doc.color})
		for team, mark in zip(teams, ("X", "O"), strict=True):
			team["team_name"] = mark
			frappe.db.set_value("GP Team", team["name"], "team_name", mark)
		ms = {
			"rules_version": 2,
			"teams": teams,
			"wins": {"X": 0, "O": 0},
			"moves": {"X": 0, "O": 0},
			"round_index": 0,
			"control_mode": ctx.configuration["control_mode"],
		}
		return self.new_board(ctx, ms)

	def members(self, ctx):
		return frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("not in", ["Kicked", "Benched", "Eliminated"])},
			fields=["name", "nickname", "team"],
			order_by="joined_at asc, name asc",
		)

	def controller(self, ms, members):
		team = ms["teams"][0 if ms["turn"] == "X" else 1]["name"]
		eligible = [p for p in members if p.team == team]
		current = next((p for p in eligible if p.name == ms.get("controller")), None)
		return current or (eligible[ms["moves"][ms["turn"]] % len(eligible)] if eligible else None)

	def select_controller(self, ctx, ms):
		ms["controller"] = None
		p = self.controller(ms, self.members(ctx))
		ms["controller"] = p.name if p else None

	def new_board(self, ctx, ms):
		ms = deepcopy(ms)
		ms.update(
			board=[""] * 9,
			turn="X" if ms["round_index"] % 2 == 0 else "O",
			winner=None,
			winning_line=[],
			last_cell=None,
			last_mark=None,
			round_key=f"board-{ms['round_index'] + 1}",
		)
		self.select_controller(ctx, ms)
		return self.transition(ctx, ms)

	def transition(self, ctx, ms, resolution=None):
		phase = "grid_round_over" if ms.get("winner") else "grid_turn"
		return Transition(
			phase=phase,
			next_ts=time.time() + 86400,
			ttl=86400,
			module_state=ms,
			resolution=resolution,
			publish={"type": "grid_conquest.updated", **self.view(ctx, ms, phase)},
		)

	def move(self, ctx, state, cell, participant=None, host=False):
		ms = state["module_state"]
		if state.get("paused"):
			frappe.throw(_("The host has paused this game"))
		actor = self.controller(ms, self.members(ctx))
		if ms["control_mode"] == "shared" or ms.get("host_turn"):
			if not host:
				frappe.throw(_("The host controls this shared board."), frappe.PermissionError)
		elif host or not actor or participant != actor.name:
			frappe.throw(_("It is another player's turn."), frappe.PermissionError)
		try:
			updated = place(ms, cell)
		except ValueError as error:
			frappe.throw(_(str(error)))
		self.select_controller(ctx, updated)
		resolution = None
		if updated["winner"]:
			deltas = []
			if updated["winner"] != "draw":
				team = updated["teams"][0 if updated["winner"] == "X" else 1]
				deltas = [
					ScoreDelta("Team", team["name"], 1, "board_win", f"board:{updated['round_index']}:win")
				]
			resolution = Resolution(
				{
					"board": updated["board"],
					"winner": updated["winner"],
					"winning_line": updated["winning_line"],
				},
				deltas,
			)
		return self.transition(ctx, updated, resolution)

	def next_board(self, ctx, state):
		ms = state["module_state"]
		if not ms.get("winner"):
			frappe.throw(_("Finish this board before starting the next."))
		if self.match_over(ms):
			return Transition(phase="podium", finished=self.finish_game(ctx, state))
		ms = deepcopy(ms)
		ms["round_index"] += 1
		return self.new_board(ctx, ms)

	def match_over(self, ms):
		return ms["round_index"] >= 2 or max(ms["wins"].values()) >= 2

	def view(self, ctx, ms, phase):
		actor = self.controller(ms, self.members(ctx))
		return {
			"rules_version": 2,
			"phase": phase,
			"board": ms["board"],
			"turn": ms["turn"],
			"wins": ms["wins"],
			"board_number": ms["round_index"] + 1,
			"winner": ms.get("winner"),
			"winning_line": ms.get("winning_line", []),
			"last_cell": ms.get("last_cell"),
			"last_mark": ms.get("last_mark"),
			"controller_name": actor.nickname if actor else None,
			"control_mode": ms["control_mode"],
			"host_turn": bool(ms.get("host_turn")),
			"match_over": bool(ms.get("winner") and self.match_over(ms)),
		}

	def serialize_public_state(self, ctx, state):
		if state["module_state"].get("rules_version") != 2:
			return super().serialize_public_state(ctx, state)
		return {
			**self.view(ctx, state["module_state"], state["phase"]),
			"revision": state["version"],
			"paused": bool(state.get("paused")),
		}

	def serialize_host_state(self, ctx, state):
		if state["module_state"].get("rules_version") != 2:
			return super().serialize_host_state(ctx, state)
		return {
			**self.serialize_public_state(ctx, state),
			"is_host": True,
			"can_move": state["phase"] == "grid_turn"
			and not state.get("paused")
			and (ctx.configuration["control_mode"] == "shared" or state["module_state"].get("host_turn")),
		}

	def serialize_player_state(self, ctx, state, participant):
		if state["module_state"].get("rules_version") != 2:
			return super().serialize_player_state(ctx, state, participant)
		ms = state["module_state"]
		actor = self.controller(ms, self.members(ctx))
		mark = next(
			(
				mark
				for mark, team in zip(("X", "O"), ms["teams"], strict=True)
				if team["name"] == participant.get("team")
			),
			None,
		)
		return {
			**self.serialize_public_state(ctx, state),
			"my_mark": mark,
			"can_move": ms["control_mode"] == "players"
			and not ms.get("host_turn")
			and not state.get("paused")
			and state["phase"] == "grid_turn"
			and bool(actor and actor.name == participant["name"]),
		}

	def finish_game(self, ctx, state):
		if ctx.configuration.get("rules_version") != 2:
			return super().finish_game(ctx, state)
		teams = frappe.db.get_values(
			"GP Team",
			filters={"session": ctx.session},
			fieldname=["name", "team_name", "color", "score"],
			as_dict=True,
			for_update=True,
			order_by="score desc, seed asc",
		)
		board = [
			{"subject_type": "Team", **t, "rank": 1 + sum(other.score > t.score for other in teams)}
			for t in teams
		]
		return GameResult({"phase": "podium", "teams": board}, board)
