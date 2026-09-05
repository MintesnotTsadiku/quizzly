"""Regression contracts for language, reconnect and distinct round progression."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from quizzly.games import GameContext
from quizzly.games.round_games.game import RoundGame
from quizzly.games.round_games.special import (
	BracketBashGame,
	EscapeTogetherGame,
	OneWordChorusGame,
	SeekAndShowGame,
	StoryLoomGame,
)


def action(player="p1", value="answer", kind="submit", name="a1"):
	return frappe._dict(
		name=name, participant=player, payload={"value": value}, action_type=kind, received_at=1
	)


class RoundRepairs(unittest.TestCase):
	def setUp(self):
		translation = patch("quizzly.games.round_games.game._", side_effect=lambda value: value)
		translation.start()
		self.addCleanup(translation.stop)
		self.ctx = GameContext("room", "123456", "common-thread", {"rounds": 3, "seconds": 30})
		self.state = {
			"phase": "round_open",
			"module_state": {"round_index": 0, "position": 1, "item": "item"},
		}
		self.item = SimpleNamespace(
			answer="ድመት", target=10, choices='["A","B"]', media_url="", prompt_text="Prompt"
		)
		self.game = RoundGame()
		self.game.key = "common-thread"

	def mocks(self, game, actions):
		return (
			patch.object(game, "item", return_value=self.item),
			patch("quizzly.games.round_games.game.accepted_actions", return_value=actions),
			patch("frappe.db", SimpleNamespace(get_value=lambda *a, **kw: "Hana")),
		)

	def test_wrong_amharic_and_empty_answers_never_score(self):
		for expected, value in [("ድመት", "ውሻ"), ("", ""), ("■■■··", "■·■■·")]:
			self.item.answer = expected
			a, b, c = self.mocks(self.game, [action(value=value)])
			with a, b, c:
				t = self.game.reveal(self.ctx, self.state)
				self.assertFalse(t.resolution.deltas)
				self.assertFalse(t.module_state["reveal"]["results"][0]["correct"])

	def test_private_response_lock_survives_new_snapshot(self):
		a, b, c = self.mocks(self.game, [action()])
		with a, b, c:
			self.assertTrue(self.game.serialize_player_state(self.ctx, self.state, {"name": "p1"})["locked"])
			self.assertFalse(self.game.serialize_player_state(self.ctx, self.state, {"name": "p2"})["locked"])

	def test_failed_number_validation(self):
		self.game.key = "closest-call"
		with patch("quizzly.games.round_games.game.accepted_actions", return_value=[]):
			for value in ["NaN", "Infinity", "-Infinity", None]:
				self.assertFalse(
					self.game.submit_action(
						self.ctx, self.state, {"name": "p1"}, "submit", {"value": value}
					).accepted
				)

	def test_creative_reveal_retains_contribution_after_reload(self):
		self.game.key = "caption-clash"
		self.state["phase"] = "vote_open"
		a, b, c = self.mocks(
			self.game, [action(value="The chair is on holiday"), action("p2", "a1", "vote", "a2")]
		)
		with a, b, c:
			t = self.game.reveal(self.ctx, self.state)
			v = self.game.serialize_public_state(self.ctx, {"phase": t.phase, "module_state": t.module_state})
			self.assertEqual(v["results"][0]["value"], "The chair is on holiday")
			self.assertEqual(v["results"][0]["points"], 750)

	def test_memory_hides_scene_and_question_in_opposite_phases(self):
		self.game.key = "memory-mosaic"
		self.item.media_url = "/scene.svg"
		a, b, c = self.mocks(self.game, [])
		with a, b, c:
			self.state["phase"] = "memory_study"
			v = self.game.serialize_public_state(self.ctx, self.state)
			self.assertEqual(v["media_url"], "/scene.svg")
			self.assertNotEqual(v["prompt"], "Prompt")
			self.state["phase"] = "round_open"
			self.assertIsNone(self.game.serialize_public_state(self.ctx, self.state)["media_url"])

	def test_story_selection_and_persistence(self):
		game = StoryLoomGame()
		self.state["module_state"]["story"] = ["Once upon a time."]
		a, b, c = self.mocks(game, [action(value="A door opened."), action("p2", "a1", "vote")])
		with a, b, c:
			t = game.reveal(self.ctx, self.state)
			self.assertEqual(t.module_state["story"], ["Once upon a time.", "A door opened."])
			self.assertEqual(t.resolution.summary["story"], t.module_state["story"])

	def test_bracket_majority_advances_and_ties_keep_seed(self):
		game = BracketBashGame()
		self.state["module_state"].update(matchup=["A", "B"], bracket_queue=["C", "D"], bracket_history=[])
		with patch(
			"quizzly.games.round_games.special.accepted_actions",
			return_value=[action(value="B"), action("p2", "B")],
		):
			t = game.reveal(self.ctx, self.state)
			self.assertEqual(t.module_state["bracket_queue"], ["C", "D", "B"])
		with patch("quizzly.games.round_games.special.accepted_actions", return_value=[]):
			t = game.reveal(self.ctx, self.state)
			self.assertTrue(t.resolution.summary["tie"])
			self.assertEqual(t.resolution.summary["answer"], "A")

	def test_chorus_duplicates_disappear_and_guesser_cannot_give_clue(self):
		game = OneWordChorusGame()
		self.state["phase"] = "chorus_clues"
		self.state["module_state"]["guesser"] = "p1"
		with patch(
			"quizzly.games.round_games.special.accepted_actions",
			return_value=[
				action("p2", "rain", "clue"),
				action("p3", "RAIN", "clue"),
				action("p4", "shelter", "clue"),
			],
		):
			t = game.advance_state(self.ctx, self.state, {"command": "next"})
			self.assertEqual(t.module_state["clues"], ["shelter"])
			self.assertFalse(
				game.submit_action(self.ctx, self.state, {"name": "p1"}, "clue", {"value": "rain"}).accepted
			)

	def test_seek_only_confirmed_missions_score(self):
		game = SeekAndShowGame()
		self.state["module_state"]["approved"] = ["p2"]
		a, b, c = self.mocks(game, [action("p1", "ball"), action("p2", "plate", name="a2")])
		with a, b, c:
			t = game.reveal(self.ctx, self.state)
			scores = {d.subject: d.points for d in t.resolution.deltas}
			self.assertEqual(scores, {"p1": 0, "p2": 250})

	def test_escape_wrong_majority_retries_stage(self):
		game = EscapeTogetherGame()
		self.state["module_state"].update(inventory=[], attempts=0)
		a, b, c = self.mocks(game, [action(value="wrong")])
		with a, b, c:
			t = game.reveal(self.ctx, self.state)
			self.assertEqual(t.module_state["position"], 0)
			self.assertFalse(t.resolution.summary["stage_passed"])


class ContentGuards(unittest.TestCase):
	def test_missing_and_unsafe_media_are_rejected(self):
		from quizzly.games.round_games.content import validate_items

		with (
			patch("quizzly.games.round_games.content._", side_effect=lambda value: value),
			patch("frappe.throw", side_effect=ValueError),
		):
			for url in [
				"",
				"javascript:alert(1)",
				"//untrusted.test/clue.svg",
				"http://untrusted.test/clue.svg",
			]:
				with self.assertRaises(ValueError):
					validate_items("picture-peek", [{"media_url": url}])
			with self.assertRaises(ValueError):
				validate_items("sound-snap", [{"media_url": "/image.svg"}])
			validate_items("sound-snap", [{"media_url": "/assets/quizzly/game-clues/ascending.wav"}])

	def test_atomic_replay_marker(self):
		from unittest.mock import MagicMock

		from quizzly.games.engine import mark_acted

		cache = MagicMock()
		cache.make_key.side_effect = lambda key: key
		cache.execute_command.side_effect = [1, 0]
		with patch("frappe.cache", cache):
			self.assertTrue(mark_acted("room", "request", 60))
			self.assertFalse(mark_acted("room", "request", 60))
		self.assertEqual(cache.execute_command.call_count, 2)
		cache.sismember.assert_not_called()
