"""Rules and role boundaries for the interactive X/O board."""

import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from quizzly.games import GameContext
from quizzly.games.grid_conquest.game import LINES, GridConquestGame, outcome, place


def initial():
	return {
		"board": [""] * 9,
		"turn": "X",
		"wins": {"X": 0, "O": 0},
		"moves": {"X": 0, "O": 0},
		"winner": None,
		"round_index": 0,
		"teams": [{"name": "x"}, {"name": "o"}],
		"control_mode": "players",
		"controller": "alice",
		"rules_version": 2,
	}


class TestGridConquest(unittest.TestCase):
	def setUp(self):
		self.game = GridConquestGame()
		self.ctx = GameContext(
			"room", "123456", "grid-conquest", {"rules_version": 2, "control_mode": "players"}
		)
		self.players = [
			SimpleNamespace(name="alice", nickname="Alice", team="x"),
			SimpleNamespace(name="bob", nickname="Bob", team="o"),
		]

	def test_every_winning_line_and_both_marks(self):
		for mark in ("X", "O"):
			for cells in LINES:
				board = [""] * 9
				for cell in cells:
					board[cell] = mark
				self.assertEqual(outcome(board), (mark, list(cells)))

	def test_alternating_moves_complete_a_real_board_once(self):
		state = initial()
		original = deepcopy(state)
		for cell in [0, 3, 1, 4, 2]:
			state = place(state, cell)
		self.assertEqual(original, initial())
		self.assertEqual(state["board"], ["X", "X", "X", "O", "O", "", "", "", ""])
		self.assertEqual(state["wins"], {"X": 1, "O": 0})
		with self.assertRaises(ValueError):
			place(state, 8)

	def test_draw_has_no_winner_or_point(self):
		state = initial()
		for cell in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
			state = place(state, cell)
		self.assertEqual(state["winner"], "draw")
		self.assertEqual(state["wins"], {"X": 0, "O": 0})

	def test_invalid_and_occupied_cells_cannot_change_state(self):
		state = place(initial(), 0)
		before = deepcopy(state)
		for cell in [0, -1, 9, "1", True, None]:
			with self.assertRaises(ValueError):
				place(state, cell)
		self.assertEqual(state, before)

	def test_private_views_expose_only_the_correct_controller(self):
		state = {"phase": "grid_turn", "version": 4, "module_state": initial()}
		with patch.object(self.game, "members", return_value=self.players):
			a = self.game.serialize_player_state(self.ctx, state, {"name": "alice", "team": "x"})
			b = self.game.serialize_player_state(self.ctx, state, {"name": "bob", "team": "o"})
			public = self.game.serialize_public_state(self.ctx, state)
		self.assertTrue(a["can_move"])
		self.assertFalse(b["can_move"])
		self.assertEqual(a["my_mark"], "X")
		self.assertEqual(b["my_mark"], "O")
		self.assertNotIn("can_move", public)
		self.assertNotIn("controller", public)

	def test_turns_rotate_within_each_side(self):
		players = [*self.players, SimpleNamespace(name="cara", nickname="Cara", team="x")]
		ms = initial()
		ms["controller"] = None
		ms["moves"]["X"] = 1
		self.assertEqual(self.game.controller(ms, players).name, "cara")
		# Joining does not steal a turn already allocated to somebody.
		ms["controller"] = "alice"
		self.assertEqual(self.game.controller(ms, players).name, "alice")
		self.assertEqual(self.game.controller(ms, players[1:]).name, "cara")

	def test_two_wins_or_three_boards_end_match(self):
		ms = initial()
		self.assertFalse(self.game.match_over(ms))
		ms["wins"]["O"] = 2
		self.assertTrue(self.game.match_over(ms))
		ms["wins"]["O"] = 0
		ms["round_index"] = 2
		self.assertTrue(self.game.match_over(ms))

	def test_second_board_starts_with_o(self):
		ms = initial()
		ms["round_index"] = 1
		with patch.object(self.game, "members", return_value=self.players):
			transition = self.game.new_board(self.ctx, ms)
		self.assertEqual(transition.module_state["turn"], "O")
		self.assertEqual(transition.module_state["controller"], "bob")

	def test_wrong_side_and_paused_moves_are_rejected(self):
		state = {"phase": "grid_turn", "version": 1, "module_state": initial()}
		with (
			patch.object(self.game, "members", return_value=self.players),
			patch("quizzly.games.grid_conquest.game._", side_effect=lambda x: x),
			patch("frappe.throw", side_effect=ValueError),
		):
			with self.assertRaises(ValueError):
				self.game.move(self.ctx, state, 0, participant="bob")
			with self.assertRaises(ValueError):
				self.game.move(self.ctx, {**state, "paused": True}, 0, participant="alice")

	def test_host_help_is_explicit_and_ends_after_one_move(self):
		ms = initial()
		ms["host_turn"] = True
		state = {"phase": "grid_turn", "version": 1, "module_state": ms}
		with patch.object(self.game, "members", return_value=self.players):
			self.assertFalse(
				self.game.serialize_player_state(self.ctx, state, {"name": "alice", "team": "x"})["can_move"]
			)
			result = self.game.move(self.ctx, state, 0, host=True)
		self.assertFalse(result.module_state["host_turn"])

	def test_no_pack_or_clock_required(self):
		config = self.game.validate_configuration(self.ctx, {"pack": "obsolete", "seconds": 15})
		self.assertEqual(
			config, {"rules_version": 2, "control_mode": "players", "boards": 3, "auto_progress": False}
		)

	def test_legacy_sessions_keep_their_original_player_view(self):
		from quizzly.games.grid_conquest.game import LegacyGrid

		with patch.object(
			LegacyGrid, "serialize_player_state", return_value={"phase": "round_open"}
		) as legacy:
			self.assertEqual(
				self.game.serialize_player_state(self.ctx, {"module_state": {}}, {"name": "alice"}),
				{"phase": "round_open"},
			)
			legacy.assert_called_once()

	def test_a_tied_match_assigns_equal_ranks(self):
		from unittest.mock import MagicMock

		import frappe

		db = MagicMock()
		db.get_values.return_value = [frappe._dict(name="x", score=1), frappe._dict(name="o", score=1)]
		with patch("frappe.db", db):
			result = self.game.finish_game(self.ctx, {})
		self.assertEqual([row["rank"] for row in result.leaderboard], [1, 1])
		self.assertTrue(db.get_values.call_args.kwargs["for_update"])

	def test_mutating_requests_restore_with_a_current_locking_read(self):
		from unittest.mock import MagicMock

		import frappe

		from quizzly.games.grid_conquest.session import restore

		db = MagicMock()
		db.get_value.side_effect = [
			frappe._dict(status="Active", game_key="grid-conquest", configuration={"rules_version": 2}),
			{"grid_snapshot": {"version": 8}},
		]
		with patch("frappe.db", db):
			self.assertEqual(restore("room", for_update=True), {"version": 8})
		self.assertTrue(db.get_value.call_args.kwargs["for_update"])
