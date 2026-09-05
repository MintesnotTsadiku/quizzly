"""Behavioral coverage for human-paced, controller-free sessions."""

import unittest
from unittest.mock import patch

from quizzly.games import GameContext
from quizzly.games.common_ground.game import CommonGroundGame


class TestCommonGround(unittest.TestCase):
	def setUp(self):
		self.game = CommonGroundGame()
		self.ctx = GameContext("room", "123456", "common-ground", {"pack": "everyday"})

	def state(self, transition):
		return {"phase": transition.phase, "module_state": transition.module_state}

	def test_starts_without_digital_participants_and_snapshots_three_prompts(self):
		first = self.game.start_game(self.ctx, [])
		self.assertEqual(first.phase, "room_prompt")
		self.assertEqual(len(first.module_state["prompts"]), 3)
		self.assertEqual(len(set(first.module_state["prompts"])), 3)
		view = self.game.serialize_public_state(self.ctx, self.state(first))
		self.assertEqual(view["round"], 1)
		self.assertNotIn("prompts", view)

	def test_deadline_never_rushes_a_conversation(self):
		first = self.game.start_game(self.ctx, [])
		for _ in range(5):
			first = self.game.advance_state(self.ctx, self.state(first), {"command": "deadline"})
		self.assertEqual(first.phase, "room_prompt")
		self.assertEqual(first.module_state["position"], 0)

	def test_three_conversations_and_shares_end_cooperatively(self):
		current = self.game.start_game(self.ctx, [])
		for round_number in range(1, 4):
			self.assertEqual(
				self.game.serialize_public_state(self.ctx, self.state(current))["round"], round_number
			)
			current = self.game.advance_state(self.ctx, self.state(current), {"command": "next"})
			self.assertEqual(current.phase, "room_share")
			current = self.game.advance_state(self.ctx, self.state(current), {"command": "next"})
		self.assertTrue(current.finished.publish["cooperative"])
		self.assertEqual(current.finished.leaderboard, [])

	def test_unknown_commands_do_not_advance(self):
		current = self.game.start_game(self.ctx, [])
		self.assertIsNone(self.game.advance_state(self.ctx, self.state(current), {"command": "guess"}))

	def test_pack_validation_and_manual_pacing(self):
		self.assertFalse(
			self.game.validate_configuration(
				self.ctx, {"pack": "imagination", "auto_progress": True, "language": "en"}
			)["auto_progress"]
		)
		with (
			patch("quizzly.games.common_ground.game._", side_effect=lambda message: message),
			patch("frappe.throw", side_effect=ValueError),
		):
			with self.assertRaises(ValueError):
				self.game.validate_configuration(self.ctx, {"pack": "missing"})
