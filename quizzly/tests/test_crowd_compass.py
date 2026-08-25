import time
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from quizzly.games import engine as gpe
from quizzly.games.api import (
	create_session,
	get_host_state,
	get_player_state,
	get_public_state,
	join_session,
	start_session,
	submit_action,
	host_command,
)


class CrowdTestCase(IntegrationTestCase):
	def make_pack(self, title: str, ranked: int = 0) -> str:
		prompts = [
			{"prompt": "Tea or coffee?", "choices": ["Tea", "Coffee"]},
			{"prompt": "Cats or dogs?", "choices": ["Cats", "Dogs"]},
			{"prompt": "Window or aisle?", "choices": ["Window", "Aisle"]},
		]
		if ranked:
			prompts = [
				{"prompt": "Rank your drinks", "choices": ["Tea", "Coffee", "Juice"]},
				{"prompt": "Rank your pets", "choices": ["Cats", "Dogs", "Fish"]},
			]
		pack = frappe.get_doc(
			{
				"doctype": "GP Crowd Pack",
				"title": title,
				"ranked": ranked,
				"prompts": [
					{"prompt_text": p["prompt"], **{f"choice_{i + 1}": c for i, c in enumerate(p["choices"])}}
					for p in prompts
				],
			}
		).insert()
		return pack.name

	def start(self, configuration: dict, players=("ada", "bob", "cy")):
		created = create_session("crowd-compass", configuration)
		self.session = created["session"]
		self.pin = created["game_pin"]
		self.players = {n: join_session(self.pin, n) for n in players}
		start_session(self.session)
		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pack = self.make_pack("CC Test Pack")
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		gpe.clear_state(getattr(self, "session", ""))
		frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, getattr(self, "session", ""))
		for dt in ("GP Score Event", "GP Action", "GP Round", "GP Team Membership"):
			for name in frappe.get_all(dt, filters={"session": getattr(self, "session", "")}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		for dt in ("GP Participant", "GP Team"):
			for name in frappe.get_all(dt, filters={"session": getattr(self, "session", "")}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		if getattr(self, "session", None):
			frappe.delete_doc("GP Session", self.session, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Crowd Pack", self.pack, force=True, ignore_permissions=True)
		if getattr(self, "extra_pack", None):
			frappe.delete_doc("GP Crowd Pack", self.extra_pack, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def token(self, nick):
		return self.players[nick]["participant_token"]

	def vote(self, nick, choice, **extra):
		return submit_action(
			self.pin, self.token(nick), "cast_vote", str(uuid.uuid4()), {"choice": choice, **extra}
		)

	def predict(self, nick, choice, estimate=None):
		payload = {"choice": choice}
		if estimate is not None:
			payload["estimate"] = estimate
		return submit_action(self.pin, self.token(nick), "make_prediction", str(uuid.uuid4()), payload)

	def tick_to(self, target, timeout=30):
		deadline = time.time() + timeout
		while time.time() < deadline:
			gpe.tick_once()
			hs = get_host_state(self.session)
			if hs.get("phase") == target or (target == "podium" and hs.get("podium")):
				return hs
			time.sleep(0.2)
		return hs


class TestConfiguration(CrowdTestCase):
	def test_defaults_normalized(self):
		from quizzly.games import GameContext
		from quizzly.games.crowd_compass.game import CrowdCompassGame

		config = CrowdCompassGame().validate_configuration(
			GameContext("", "", "crowd-compass", {}), {"pack": self.pack}
		)
		self.assertEqual(config["vote_seconds"], 15)
		self.assertEqual(config["scoring_mode"], "Individual")
		self.assertFalse(config["estimation"])
		self.assertTrue(config["room_match"])

	def test_bad_stage_rejected(self):
		from quizzly.games import GameContext
		from quizzly.games.crowd_compass.game import CrowdCompassGame

		with self.assertRaises(frappe.ValidationError):
			CrowdCompassGame().validate_configuration(
				GameContext("", "", "crowd-compass", {}), {"pack": self.pack, "vote_seconds": 7}
			)

	def test_team_match_requires_team_mode(self):
		from quizzly.games import GameContext
		from quizzly.games.crowd_compass.game import CrowdCompassGame

		config = CrowdCompassGame().validate_configuration(
			GameContext("", "", "crowd-compass", {}),
			{"pack": self.pack, "scoring_mode": "Individual", "team_match": 1},
		)
		self.assertFalse(config["team_match"])


class TestRoundScoring(CrowdTestCase):
	def start_simple(self, **overrides):
		config = {
			"pack": self.pack,
			"vote_seconds": 10,
			"prediction_seconds": 10,
			"estimation": 1,
			"room_match": 1,
		}
		config.update(overrides)
		self.start(config)

	def test_full_round_scores_prediction_match_and_estimation(self):
		self.start_simple()
		hs = self.tick_to("prompt_open")
		self.assertIsNotNone(hs, "never reached prompt_open")
		# ada+bob vote Tea, cy votes Coffee
		self.vote("ada", "1")
		self.vote("bob", "1")
		self.vote("cy", "2")
		prompt_view = get_public_state(self.pin)["view"]
		self.assertEqual(prompt_view["voted"], 3)
		# distribution stays hidden during voting
		self.assertNotIn("distribution", prompt_view)

		reveal_ready = self.tick_to("prediction_open")
		self.assertEqual(reveal_ready["view"]["voted"], 3)
		# everyone predicts Tea; ada nails the share (2/3 = 67%), bob is off, cy way off
		self.predict("ada", "1", estimate=67)
		self.predict("bob", "1", estimate=20)
		self.predict("cy", "2", estimate=90)

		reveal = self.tick_to("reveal", timeout=self.SECONDS + 20)
		self.assertIsNotNone(reveal, "never reached reveal")
		self.assertEqual(reveal["view"]["plurality"], ["1"])
		self.assertEqual(reveal["view"]["distribution"], {"1": 2, "2": 1})

		# ledger: 2x +500 predictions, ada +300 estimation, ada+bob +100 room match
		events = frappe.get_all(
			"GP Score Event",
			filters={"session": self.session},
			fields=["subject", "points", "category"],
		)
		by_category = {}
		for e in events:
			by_category.setdefault(e.category, []).append(e.points)
		self.assertEqual(sorted(by_category["correct_prediction"]), [500, 500])
		self.assertEqual(by_category.get("estimation_bonus"), [300])
		self.assertEqual(sorted(by_category.get("room_match", [])), [100, 100])

		# private points: ada 500+300+100=900, bob 500+100=600, cy 0
		ada = get_player_state(self.pin, self.token("ada"))
		bob = get_player_state(self.pin, self.token("bob"))
		cy = get_player_state(self.pin, self.token("cy"))
		self.assertEqual(ada["view"]["my_points"], 900)
		self.assertEqual(bob["view"]["my_points"], 600)
		self.assertEqual(cy["view"]["my_points"], 0)

	def test_tied_pluralities_both_win(self):
		self.start_simple()
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		self.vote("bob", "2")
		self.tick_to("prediction_open")
		self.predict("ada", "1", estimate=50)
		self.predict("cy", "2", estimate=50)
		reveal = self.tick_to("reveal", timeout=self.SECONDS + 20)
		self.assertEqual(sorted(reveal["view"]["plurality"]), ["1", "2"])
		events = frappe.get_all(
			"GP Score Event",
			filters={"session": self.session, "category": "correct_prediction"},
			pluck="points",
		)
		self.assertEqual(sorted(events), [500, 500])

	def test_quorum_miss_voids_scoring(self):
		self.start_simple(quorum=3)
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		self.tick_to("prediction_open")
		self.predict("ada", "1", estimate=100)
		reveal = self.tick_to("reveal", timeout=self.SECONDS + 20)
		self.assertFalse(reveal["view"]["quorum_met"])
		self.assertEqual(frappe.db.count("GP Score Event", {"session": self.session}), 0)

	def test_duplicate_vote_rejected(self):
		self.start_simple()
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		with self.assertRaises(frappe.ValidationError):
			self.vote("ada", "2")

	def test_nonresponse_scores_nothing(self):
		self.start_simple()
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		self.tick_to("prediction_open")
		self.predict("ada", "1", estimate=100)
		# bob and cy abstain from both stages
		self.tick_to("scoreboard", timeout=self.SECONDS * 2 + 20)
		cy = get_player_state(self.pin, self.token("cy"))
		self.assertEqual(cy["score"], 0)

	SECONDS = 10


class TestRanked(CrowdTestCase):
	def start_ranked(self):
		self.extra_pack = self.make_pack("Ranked Pack", ranked=1)
		self.start(
			{
				"pack": self.extra_pack,
				"vote_seconds": 10,
				"prediction_seconds": 10,
				"ranked_from_pack": 1,
			}
		)

	def test_weighted_aggregation_and_second_pick(self):
		self.start_ranked()
		hs = self.tick_to("prompt_open")
		self.assertTrue(hs["view"]["ranked"])
		# ranked packs take first + second
		r = submit_action(
			self.pin, self.token("ada"), "cast_vote", str(uuid.uuid4()), {"choice": "1", "second": "2"}
		)
		self.assertEqual(r["second"], "2")
		self.vote("bob", "1", second="3")
		# second equals first -> rejected
		with self.assertRaises(frappe.ValidationError):
			submit_action(
				self.pin, self.token("cy"), "cast_vote", str(uuid.uuid4()), {"choice": "1", "second": "1"}
			)
		self.vote("cy", "2", second="1")
		self.tick_to("prediction_open")
		self.predict("ada", "1", estimate=80)
		from quizzly.games.crowd_compass.game import CrowdCompassGame

		preview = CrowdCompassGame().reveal(gpe.context_for(frappe.get_doc("GP Session", self.session)), gpe.get_state(self.session))
		self.assertEqual(preview.publish["distribution"], {"1": 5, "2": 3, "3": 1})
		reveal = self.tick_to("reveal", timeout=40)
		# weighted: ada (1,2) -> Tea 2 + Coffee 1; bob (1,3) -> Tea 2 + Juice 1; cy (2,1) -> Coffee 2 + Tea 1
		self.assertEqual(reveal["view"]["plurality"], ["1"])
		self.assertEqual(reveal["view"]["distribution"]["1"], 5)
		self.assertEqual(reveal["view"]["distribution"]["2"], 3)
		self.assertEqual(reveal["view"]["distribution"]["3"], 1)


class TestTeamAverage(CrowdTestCase):
	def test_team_podium_averages_members(self):
		self.start(
			{
				"pack": self.pack,
				"vote_seconds": 10,
				"prediction_seconds": 10,
				"scoring_mode": "Team average",
				"teams_count": 2,
				"team_match": 1,
				"rounds": 1,
			}
		)
		hs = self.tick_to("prompt_open")
		self.assertEqual(len(hs["view"]["teams"]), 2)
		# map each nick to their team row
		team_of = {}
		for nick in self.players:
			joined = self.players[nick]["participant"]
			team_of[nick] = next(t for t in hs["view"]["teams"] if t["name"] == self.players[nick].get("team") or self.member_team(joined) == t["name"])

		# everyone votes choice 1; predictions: ada+bob correct, cy wrong
		for nick in self.players:
			self.vote(nick, "1")
		self.tick_to("prediction_open")
		for nick in self.players:
			if nick != "cy":
				self.predict(nick, "1")
			else:
				self.predict("cy", "2")
		podium = self.tick_to("podium", timeout=80)
		self.assertIsNotNone(podium, "game never finished")
		# display score is the AVERAGE of the members' ledger scores
		for team in podium["podium"]:
			member_rows = frappe.get_all(
				"GP Participant", filters={"team": team["name"]}, fields=["name", "score"]
			)
			expected = round(sum(m.score for m in member_rows) / len(member_rows))
			self.assertEqual(team["score"], expected)

	def member_team(self, participant: str) -> str | None:
		return frappe.db.get_value("GP Participant", participant, "team")


class TestHostPowers(CrowdTestCase):
	def test_void_prompt_reverses_deltas(self):
		self.start(
			{"pack": self.pack, "vote_seconds": 10, "prediction_seconds": 10, "room_match": 1}
		)
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		self.vote("bob", "1")
		self.tick_to("prediction_open")
		self.predict("ada", "1")
		self.predict("bob", "1")
		self.tick_to("scoreboard", timeout=45)
		before = frappe.db.get_value("GP Participant", self.players["ada"]["participant"], "score")
		self.assertEqual(before, 600)  # 500 + 100

		host_command(self.session, "void_prompt", {})
		self.tick_to("scoreboard", timeout=10)
		after = frappe.db.get_value("GP Participant", self.players["ada"]["participant"], "score")
		self.assertEqual(after, 0)
		reversals = frappe.get_all(
			"GP Score Event", filters={"session": self.session, "category": "void_reversal"}, pluck="points"
		)
		# one compensating event per original ledger row
		self.assertEqual(sorted(reversals), [-500, -500, -100, -100])

	def test_second_prompt_events_and_void_keep_their_round(self):
		self.start(
			{
				"pack": self.pack,
				"vote_seconds": 10,
				"prediction_seconds": 10,
				"room_match": 1,
				"rounds": 2,
			}
		)
		for expected_round in (0, 1):
			self.tick_to("prompt_open", timeout=20)
			self.vote("ada", "1")
			self.tick_to("prediction_open", timeout=20)
			self.predict("ada", "1")
			self.tick_to("scoreboard", timeout=45)
			indices = frappe.get_all(
				"GP Score Event",
				filters={"session": self.session, "category": ("!=", "void_reversal")},
				pluck="round_index",
			)
			self.assertIn(expected_round, indices)
			if expected_round == 0:
				host_command(self.session, "skip_turn", {})

		before = frappe.db.get_value("GP Participant", self.players["ada"]["participant"], "score")
		host_command(self.session, "void_prompt", {})
		self.tick_to("scoreboard", timeout=10)
		after = frappe.db.get_value("GP Participant", self.players["ada"]["participant"], "score")
		self.assertEqual(before - after, 600)
		self.assertTrue(
			frappe.get_all(
				"GP Score Event",
				filters={"session": self.session, "round_index": 1, "category": "void_reversal"},
			)
		)

	def test_live_prompt_on_blank_room(self):
		self.start({"vote_seconds": 10, "prediction_seconds": 10})
		hs = self.tick_to("intermission")
		self.assertIsNotNone(hs, "blank room never reached intermission")
		host_command(
			self.session,
			"push_prompt",
			{"prompt": "Sunrise or sunset?", "choice_1": "Sunrise", "choice_2": "Sunset"},
		)
		hs = self.tick_to("prompt_open", timeout=15)
		self.assertIsNotNone(hs)
		self.assertEqual(hs["view"]["prompt"], "Sunrise or sunset?")
		self.vote("ada", "1")
		self.vote("bob", "2")
		self.vote("cy", "1")
		self.tick_to("prediction_open")
		self.predict("ada", "1", estimate=67)
		podium = self.tick_to("podium", timeout=60)
		self.assertIsNotNone(podium, "blank room never finished")
		self.assertEqual(podium["podium"][0]["team_name"], "ada")


class TestSecrecy(CrowdTestCase):
	def test_vote_and_prediction_snapshots_leak_nothing(self):
		self.start({"pack": self.pack, "vote_seconds": 10, "prediction_seconds": 10})
		self.tick_to("prompt_open")
		self.vote("ada", "1")
		self.vote("bob", "1")
		public = get_public_state(self.pin)
		blob = str(public["view"]).lower()
		self.assertNotIn("distribution", blob)
		self.assertNotIn("tally", blob)
		self.assertNotIn("plurality", blob)
		pred = self.tick_to("prediction_open")
		blob = str(pred["view"]).lower()
		self.assertNotIn("distribution", blob)
		ada = get_player_state(self.pin, self.token("ada"))
		self.assertEqual(ada["view"]["my_vote"], "1")
		self.assertNotIn("my_vote", str(get_public_state(self.pin)["view"]))
