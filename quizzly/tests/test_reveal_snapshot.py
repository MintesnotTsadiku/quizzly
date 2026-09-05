"""A late projector/reload must preserve participation counts on the reveal."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from quizzly.games import GameContext
from quizzly.games.crowd_compass.game import CrowdCompassGame


class TestRevealSnapshot(unittest.TestCase):
	def test_reveal_snapshot_counts_predictions_as_well_as_votes(self):
		ctx = GameContext("session", "123456", "crowd-compass", {"ranked": False, "quorum": 1})
		state = {
			"module_state": {
				"round_index": 0,
				"current": {"choices": [{"id": "1"}, {"id": "2"}]},
				"plurality": ["1"],
			}
		}
		actions = [
			SimpleNamespace(action_type="cast_vote", payload={"choice": "1"}),
			SimpleNamespace(action_type="make_prediction", payload={"choice": "1"}),
		]
		with patch("quizzly.games.crowd_compass.game.accepted_actions", return_value=actions):
			view = CrowdCompassGame().reveal_view(ctx, state)
		self.assertEqual(view["votes"], 1)
		self.assertEqual(view["predictions"], 1)
