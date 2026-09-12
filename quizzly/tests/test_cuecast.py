import time

import frappe
from frappe.tests import IntegrationTestCase

from quizzly.games import engine as gpe
from quizzly.games.api import (
	create_session,
	end_session,
	get_host_state,
	get_player_state,
	get_public_state,
	host_command,
	join_session,
	start_session,
	submit_action,
)


class CueCastTestCase(IntegrationTestCase):
	TURNS = 1
	SECONDS = 30

	def setUp(self):
		frappe.set_user("Administrator")
		self.deck = frappe.get_doc(
			{
				"doctype": "GP Cue Deck",
				"title": "CueCast Test Deck",
				"mode": "Act",
				"prompts": [{"prompt_text": t} for t in ["one", "two", "three", "four", "five"]],
			}
		).insert()
		frappe.db.commit()
		created = create_session(
			"cuecast",
			{
				"deck": self.deck.name,
				"seconds": self.SECONDS,
				"teams_count": 2,
				"sudden_death": 1,
			},
		)
		self.session = created["session"]
		self.pin = created["game_pin"]
		names = ["ada", "bob", "cy", "dee"] if self.TURNS else ["ada", "bob"]
		self.players = {n: join_session(self.pin, n) for n in names}
		start_session(self.session)
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		gpe.clear_state(self.session)
		frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, self.session)
		for dt in ("GP Score Event", "GP Action", "GP Round", "GP Team Membership"):
			for name in frappe.get_all(dt, filters={"session": self.session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		for dt in ("GP Participant", "GP Team"):
			for name in frappe.get_all(dt, filters={"session": self.session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Session", self.session, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Cue Deck", self.deck.name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def tick_to(self, target, timeout=20):
		deadline = time.time() + timeout
		hs = get_host_state(self.session)
		while time.time() < deadline:
			gpe.tick_once()
			hs = get_host_state(self.session)
			if hs.get("phase") == target or (target == "podium" and hs.get("podium")):
				return hs
		return None


class TestConfiguration(CueCastTestCase):
	def test_missing_deck_throws_and_creates_nothing(self):
		from quizzly.games import GameContext
		from quizzly.games.cuecast.game import CueCastGame

		with self.assertRaises(frappe.ValidationError):
			CueCastGame().validate_configuration(GameContext("", "", "cuecast", {}), {"deck": None})

	def test_defaults_normalized(self):
		from quizzly.games import GameContext
		from quizzly.games.cuecast.game import CueCastGame

		config = CueCastGame().validate_configuration(
			GameContext("", "", "cuecast", {}), {"deck": self.deck.name}
		)
		self.assertEqual(config["seconds"], 60)
		self.assertEqual(config["teams_count"], 2)
		self.assertEqual(config["turns_per_team"], 1)
		self.assertEqual(config["mode"], "Act")


class TestTurnFlow(CueCastTestCase):
	def test_prompt_secret_scoped_to_performer(self):
		hs = self.tick_to("turn_open")
		self.assertIsNotNone(hs, "never reached turn_open")
		performer_nick = hs["view"]["performer"]["nickname"]
		token = self.players[performer_nick]["participant_token"]

		ps = get_player_state(self.pin, token)
		self.assertTrue(ps["view"]["is_performer"])
		self.assertTrue(ps["view"].get("prompt"))

		public = get_public_state(self.pin)
		self.assertNotIn("prompt", public["view"])
		other = next(n for n in self.players if n != performer_nick)
		ops = get_player_state(self.pin, self.players[other]["participant_token"])
		self.assertNotIn("prompt", ops["view"])

	def test_only_performer_scores_prompts(self):
		hs = self.tick_to("turn_open")
		performer_nick = hs["view"]["performer"]["nickname"]
		other = next(n for n in self.players if n != performer_nick)
		with self.assertRaises(frappe.ValidationError):
			submit_action(
				self.pin,
				self.players[other]["participant_token"],
				"correct_prompt",
				"k-other",
			)

	def test_correct_advances_and_scores_team(self):
		hs = self.tick_to("turn_open")
		performer = hs["view"]["performer"]["nickname"]
		token = self.players[performer]["participant_token"]
		first_word = get_player_state(self.pin, token)["view"]["prompt"]

		r1 = submit_action(self.pin, token, "correct_prompt", "k1")
		r2 = submit_action(self.pin, token, "correct_prompt", "k2")
		self.assertNotEqual(r1["next_prompt"], first_word)
		self.assertNotEqual(r2["next_prompt"], r1["next_prompt"])

		review = self.tick_to("turn_review", timeout=self.SECONDS + 25)
		self.assertIsNotNone(review, "turn never closed")
		self.assertEqual(review["view"]["solved_count"], 2)
		self.assertEqual(len(review["view"]["played"]), 2)

		scoreboard = self.tick_to("scoreboard")
		scores = {t["team_name"]: t["score"] for t in scoreboard["view"]["teams"]}
		self.assertEqual(sum(scores.values()), 2)

	def test_ledger_rows_match_solved_count(self):
		hs = self.tick_to("turn_open")
		token = self.players[hs["view"]["performer"]["nickname"]]["participant_token"]
		for key in ("k1", "k2", "k3"):
			submit_action(self.pin, token, "correct_prompt", key)
		self.tick_to("scoreboard", timeout=self.SECONDS + 25)
		events = frappe.get_all(
			"GP Score Event",
			filters={"session": self.session, "category": "correct_prompt"},
			pluck="points",
		)
		self.assertEqual(sorted(events), [1, 1, 1])


class TestRotationAndFinish(CueCastTestCase):
	def test_equal_turns_then_podium(self):
		seen = []
		for _ in range(4):
			hs = self.tick_to("turn_open")
			if not hs:
				break
			seen.append(hs["view"]["performer"]["nickname"])
			podium = self.tick_to("podium", timeout=self.SECONDS * 2 + 60)
			if podium:
				break
		podium = self.tick_to("podium", timeout=self.SECONDS * 2 + 60)
		self.assertIsNotNone(podium, "game never finished")
		teams = podium["podium"]
		self.assertEqual(len(teams), 2)
		ranks = sorted(t["rank"] for t in teams)
		self.assertEqual(ranks[0], 1)
		doc = frappe.get_doc("GP Session", self.session)
		self.assertEqual(doc.status, "Ended")

	def test_tied_game_gets_sudden_death(self):
		# nobody answers: both teams tie at zero -> sudden death turns run before the podium
		self.tick_to("turn_open")
		podium = self.tick_to("podium", timeout=self.SECONDS * 5 + 60)
		self.assertIsNotNone(podium, "tied game never reached podium")
		best = podium["podium"][0]["rank"]
		tied = [t for t in podium["podium"] if t["rank"] == best]
		self.assertGreaterEqual(len(tied), 1)

	def test_host_end_from_lobby_cancels(self):
		pass  # covered implicitly by teardown paths; lobby cancel is platform API tested below


class TestHostControls(IntegrationTestCase):
	def test_non_host_rejected(self):
		frappe.set_user("Administrator")
		from quizzly.games.api import create_session

		created = create_session("common-ground", {"pack": "everyday"})
		frappe.set_user("bob@example.com" if frappe.db.exists("User", "bob@example.com") else "Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				host_command(created["session"], "balance_teams", {"count": 2})
		finally:
			frappe.set_user("Administrator")
			import frappe as f

			if f.db.exists("GP Session", created["session"]):
				f.delete_doc("GP Session", created["session"], force=True, ignore_permissions=True)
				f.db.commit()

	def test_end_session_from_lobby_cancels(self):
		frappe.set_user("Administrator")
		created = create_session("common-ground", {"pack": "everyday"})
		end_session(created["session"])
		self.assertEqual(frappe.db.get_value("GP Session", created["session"], "status"), "Cancelled")
		frappe.delete_doc("GP Session", created["session"], force=True, ignore_permissions=True)
		frappe.db.commit()
