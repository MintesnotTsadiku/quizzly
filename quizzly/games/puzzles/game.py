"""Human-paced, durable room puzzles with game-specific rules."""

import time
from copy import deepcopy

import frappe
from frappe import _

from quizzly.games import GameManifest, GameResult, Resolution, ScoreDelta, Transition
from quizzly.games.round_games.game import PROFILES, RoundGame

from . import rules


class PuzzleGame(RoundGame):
	@property
	def manifest(self):
		return GameManifest(
			self.key,
			PROFILES[self.key][0],
			"2.0.0",
			PROFILES[self.key][1],
			2 if self.key == "dots-and-boxes" else 1,
			None,
			"One room · shared board or playing devices",
			10,
			("board", "puzzle"),
			"Beta",
			("board", "reconnect"),
			("next", "pause", "resume"),
			self.key,
		)

	def validate_configuration(self, ctx, cfg):
		mode = cfg.get("control_mode", "players")
		if mode not in ("players", "shared"):
			frappe.throw(_("Choose a control mode."))
		return {"rules_version": 2, "control_mode": mode, "auto_progress": False}

	def start_game(self, ctx, participants):
		if ctx.configuration.get("rules_version") != 2:
			return super().start_game(ctx, participants)
		ms = {
			"rules_version": 2,
			"round_index": 0,
			"round_key": "puzzle-1",
			"puzzle": rules.initial(self.key),
		}
		if self.key == "dots-and-boxes":
			from quizzly.games import engine

			if ctx.configuration["control_mode"] == "players" and len(participants) < 2:
				frappe.throw(_("Two playing devices are needed. Or choose one shared board."))
			if len(participants) >= 2:
				teams = engine.create_teams(ctx.session, participants, 2)
			else:
				teams = []
				for side in ("X", "O"):
					team = frappe.get_doc(
						{
							"doctype": "GP Team",
							"session": ctx.session,
							"team_name": side,
							"seed": len(teams) + 1,
							"color": "ember" if side == "X" else "lagoon",
						}
					).insert(ignore_permissions=True)
					teams.append({"name": team.name})
			for side, team in zip(("X", "O"), teams, strict=True):
				frappe.db.set_value("GP Team", team["name"], "team_name", side)
			ms["puzzle"]["teams"] = [team["name"] for team in teams]
		return self.transition(ctx, ms)

	def transition(self, ctx, ms):
		phase = "puzzle_complete" if ms["puzzle"]["done"] else "puzzle_play"
		resolution = None
		if ms["puzzle"]["done"] and self.key == "dots-and-boxes":
			p = ms["puzzle"]
			resolution = Resolution(
				{"scores": p["scores"]},
				[
					ScoreDelta("Team", team, p["scores"][side], "territory", f"dots:final:{team}")
					for side, team in zip(("X", "O"), p["teams"], strict=True)
				],
			)
		return Transition(
			resolution=resolution,
			phase=phase,
			next_ts=time.time() + 86400,
			ttl=86400,
			module_state=ms,
			publish={"type": f"{self.key.replace('-', '_')}.updated", "phase": phase},
		)

	def puzzle_command(self, ctx, state, action, payload, participant=None):
		if state.get("paused"):
			frappe.throw(_("Resume the game first."))
		if participant and ctx.configuration["control_mode"] == "shared":
			frappe.throw(_("The host controls this shared board."))
		if participant and self.key == "dots-and-boxes":
			controller = self.controller(ctx, state["module_state"]["puzzle"])
			if not controller or controller["name"] != participant:
				frappe.throw(_("Wait for your turn."))
		ms = deepcopy(state["module_state"])
		try:
			ms["puzzle"] = rules.apply(ms["puzzle"], action, payload)
		except ValueError as e:
			frappe.throw(_(str(e)))
		return self.transition(ctx, ms)

	def next_board(self, ctx, state):
		if not state["module_state"]["puzzle"]["done"]:
			frappe.throw(_("Finish the puzzle first."))
		return Transition(phase="podium", finished=self.finish_game(ctx, state))

	def members(self, ctx):
		return frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("not in", ["Kicked", "Benched", "Eliminated"])},
			fields=["name", "nickname", "team"],
			order_by="joined_at asc, name asc",
		)

	def controller(self, ctx, puzzle):
		if self.key != "dots-and-boxes" or ctx.configuration["control_mode"] == "shared":
			return None
		members = self.members(ctx)
		side = 0 if puzzle["turn"] == "X" else 1
		eligible = [p for p in members if p["team"] == puzzle["teams"][side]]
		return eligible[puzzle["side_moves"][puzzle["turn"]] % len(eligible)] if eligible else None

	def serialize_public_state(self, ctx, state):
		if ctx.configuration.get("rules_version") != 2:
			return super().serialize_public_state(ctx, state)
		puzzle = state["module_state"]["puzzle"]
		controller = self.controller(ctx, puzzle)
		return {
			"rules_version": 2,
			"phase": state["phase"],
			"puzzle": puzzle,
			"revision": state["version"],
			"paused": bool(state.get("paused")),
			"controller": controller,
			"control_mode": ctx.configuration["control_mode"],
		}

	def serialize_player_state(self, ctx, state, participant):
		if ctx.configuration.get("rules_version") != 2:
			return super().serialize_player_state(ctx, state, participant)
		view = self.serialize_public_state(ctx, state)
		if self.key == "dots-and-boxes":
			teams = state["module_state"]["puzzle"]["teams"]
			view["my_side"] = (
				("X", "O")[teams.index(participant.get("team"))] if participant.get("team") in teams else None
			)
		view["can_move"] = ctx.configuration["control_mode"] == "players" and (
			self.key != "dots-and-boxes" or (view["controller"] or {}).get("name") == participant["name"]
		)
		return view

	def serialize_host_state(self, ctx, state):
		if ctx.configuration.get("rules_version") != 2:
			return super().serialize_host_state(ctx, state)
		return {**self.serialize_public_state(ctx, state), "can_move": True, "is_host": True}

	def finish_game(self, ctx, state):
		if ctx.configuration.get("rules_version") != 2:
			return super().finish_game(ctx, state)
		puzzle = state["module_state"]["puzzle"]
		board = []
		if self.key == "dots-and-boxes":
			for side, team in zip(("X", "O"), puzzle["teams"], strict=True):
				board.append(
					{
						"subject_type": "Team",
						"name": team,
						"team_name": side,
						"score": puzzle["scores"][side],
						"rank": 1 if puzzle["scores"][side] == max(puzzle["scores"].values()) else 2,
					}
				)
		return GameResult({"phase": "podium", "puzzle": puzzle}, board)


DotsAndBoxesGame = type("DotsAndBoxesGame", (PuzzleGame,), {"key": "dots-and-boxes"})
GroupSudokuGame = type("GroupSudokuGame", (PuzzleGame,), {"key": "group-sudoku"})
PathWeaverGame = type("PathWeaverGame", (PuzzleGame,), {"key": "path-weaver"})
HiddenPictureGame = type("HiddenPictureGame", (PuzzleGame,), {"key": "hidden-picture"})
QuiltPuzzleGame = type("QuiltPuzzleGame", (PuzzleGame,), {"key": "quilt-puzzle"})
