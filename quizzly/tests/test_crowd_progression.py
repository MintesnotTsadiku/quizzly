"""Deterministic scoring and recap tests; no site data or background jobs."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from quizzly.games import GameContext
from quizzly.games.crowd_compass.game import CrowdCompassGame
from quizzly.games.crowd_compass.progression import recap_from_rounds, round_arc


class TestCrowdProgression(unittest.TestCase):
	def setUp(self):
		self.game = CrowdCompassGame()
		self.ctx = GameContext(
			"session",
			"123456",
			"crowd-compass",
			dict(
				gathering_arc=True,
				ranked=False,
				quorum=1,
				estimation=False,
				room_match=True,
				team_match=False,
				vote_seconds=10,
			),
		)
		self.prompt = {
			"prompt": "Stay in or go out?",
			"choices": [{"id": "1", "text": "Stay in"}, {"id": "2", "text": "Go out"}],
		}

	def test_legacy_short_classic_and_extra_rounds(self):
		for enabled, number, planned in [(None, 3, 3), (False, 3, 3), (True, 2, 2), (True, 4, 3)]:
			self.assertEqual(round_arc(enabled, number, planned)["prediction_points"], 500)
		self.assertEqual(
			[round_arc(True, n, 3)["chapter"] for n in range(1, 5)], ["opening", "build", "finale", "encore"]
		)

	def test_finale_doubles_prediction_only_and_dedupe_keys_stay_stable(self):
		actions = [
			SimpleNamespace(name="v", participant="p", action_type="cast_vote", payload={"choice": "1"}),
			SimpleNamespace(
				name="p", participant="p", action_type="make_prediction", payload={"choice": "1"}
			),
		]
		for number, points in [(1, 500), (3, 1000), (4, 500)]:
			state = {
				"module_state": {
					"round_index": number - 1,
					"position": number,
					"queue": [self.prompt] * 4,
					"current": self.prompt,
					"arc": round_arc(True, number, 3),
				}
			}
			with (
				patch("quizzly.games.crowd_compass.game.accepted_actions", return_value=actions),
				patch.object(self.game, "standings", return_value={}),
			):
				result = self.game.reveal(self.ctx, state)
				again = self.game.reveal(self.ctx, state)
			self.assertEqual(
				[(d.category, d.points) for d in result.resolution.deltas],
				[("correct_prediction", points), ("room_match", 100)],
			)
			self.assertEqual(result.resolution.deltas, again.resolution.deltas)
			self.assertEqual(recap_from_rounds([result.resolution.summary])["moments"][0]["percent"], 100)

	def test_finale_preserves_team_and_estimation_bonuses(self):
		self.ctx.configuration.update(team_match=True, estimation=True)
		actions = [
			SimpleNamespace(name="v", participant="p", action_type="cast_vote", payload={"choice": "1"}),
			SimpleNamespace(
				name="p",
				participant="p",
				action_type="make_prediction",
				payload={"choice": "1", "estimate": 100},
			),
		]
		state = {
			"module_state": {
				"round_index": 2,
				"position": 3,
				"queue": [self.prompt] * 3,
				"current": self.prompt,
				"arc": round_arc(True, 3, 3),
			}
		}
		with (
			patch("quizzly.games.crowd_compass.game.accepted_actions", return_value=actions),
			patch.object(self.game, "standings", return_value={}),
			patch.object(self.game, "team_of", return_value="team"),
			patch.object(self.game, "team_plurality", return_value=["1"]),
		):
			result = self.game.reveal(self.ctx, state)
		self.assertEqual(
			{d.category: d.points for d in result.resolution.deltas},
			{"correct_prediction": 1000, "room_match": 100, "team_match": 100, "estimation_bonus": 300},
		)

	def test_extra_prompt_does_not_move_announced_finale(self):
		state = {
			"phase": "prompt_open",
			"next_ts": 12345678900,
			"module_state": {
				"position": 1,
				"round_index": 0,
				"queue": [self.prompt] * 3,
				"planned_rounds": 3,
				"arc": round_arc(True, 1, 3),
			},
		}
		added = self.game.push_prompt(
			self.ctx, state, {"prompt": "Encore?", "choice_1": "Yes", "choice_2": "No"}
		)
		self.assertEqual(added.module_state["queue"][2], self.prompt)
		self.assertEqual(added.module_state["queue"][3]["prompt"], "Encore?")
		self.assertEqual(added.module_state["arc"], state["module_state"]["arc"])
		added.module_state.update(position=2, round_index=1)
		with patch.object(self.game, "standings", return_value={}):
			finale = self.game.open_prompt(self.ctx, added.module_state)
		self.assertEqual(finale.publish["arc"]["prediction_points"], 1000)

	def test_void_reverses_actual_finale_score_once(self):
		state = {"phase": "reveal", "next_ts": 12345678900, "module_state": {"round_index": 2, "voided": []}}
		events = [
			SimpleNamespace(
				subject_type="Participant", subject="p", points=1000, idempotency_key="r2:p:predict"
			)
		]
		with (
			patch("frappe.db", SimpleNamespace(get_value=lambda *a: "round")),
			patch("frappe.get_all", return_value=events),
		):
			result = self.game.void_prompt(self.ctx, state)
			self.assertEqual(result.resolution.deltas[0].points, -1000)
			self.assertIsNone(self.game.void_prompt(self.ctx, {**state, "module_state": result.module_state}))
		self.assertEqual(recap_from_rounds([result.resolution.summary])["rounds_completed"], 0)

	def test_recap_excludes_void_ties_no_quorum_and_private_details(self):
		base = {
			**self.prompt,
			"tally": {"1": 2, "2": 1},
			"plurality": ["1"],
			"quorum_met": True,
			"votes": 3,
			"participant": "private-name",
			"token": "secret",
		}
		result = recap_from_rounds(
			[base, {**base, "voided": 0}, {**base, "plurality": ["1", "2"]}, {**base, "quorum_met": False}]
		)
		self.assertEqual(result["rounds_completed"], 3)
		self.assertEqual(
			result["moments"],
			[{"prompt": self.prompt["prompt"], "choice": "Stay in", "percent": 67, "ranked": False}],
		)
		self.assertTrue(recap_from_rounds([{**base, "ranked": True}])["moments"][0]["ranked"])
