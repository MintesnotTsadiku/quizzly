import frappe
from frappe.tests import IntegrationTestCase

from quizzly import engine
from quizzly.api import get_host_state, get_result, get_state, join_session, submit_answer
from quizzly.profanity import is_profane
from quizzly.tests.test_engine import GameTestCase


class TestProfanityFilter(IntegrationTestCase):
	def test_clean_nicknames_pass(self):
		for nickname in ("Alice", "xX_Dragon_Xx", "Scott", "assassin_42", "Class1"):
			self.assertFalse(is_profane(nickname), nickname)

	def test_dirty_nicknames_blocked(self):
		for nickname in ("fuck", "Sh1tLord", "b i t c h", "@sshole", "n1gger"):
			self.assertTrue(is_profane(nickname), nickname)


class TestJoinFiltersNicknames(GameTestCase):
	def test_profane_nickname_rejected_with_message(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			join_session(self.pin, "fuckface")
		self.assertIn("nickname", str(caught.exception).lower())


class TestHostState(GameTestCase):
	def test_lobby_state(self):
		state = get_host_state(self.session)
		self.assertEqual(state["game_pin"], self.pin)
		self.assertEqual(state["status"], "Lobby")
		self.assertEqual(len(state["participants"]), 2)

	def test_finds_live_session_without_argument(self):
		self.assertEqual(get_host_state()["session"], self.session)

	def test_mid_question_state_carries_correct_option_for_host(self):
		self.activate()
		question = self.open_question(window=30)
		submit_answer(self.pin, self.alice["participant_token"], question.name, "2")

		state = get_host_state(self.session)
		self.assertEqual(state["phase"], "question")
		self.assertEqual(state["answer_count"], 1)
		self.assertGreater(state["remaining_seconds"], 25)
		self.assertEqual(state["question"]["correct_option"], question.correct_option)

	def test_non_host_is_refused(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_host_state(self.session)


class TestPlayerResult(GameTestCase):
	def test_result_reports_own_outcome_and_rank(self):
		self.activate()
		question = self.open_question(window=30)
		submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		engine.close_question(self.session_doc, question, 0, len(self.questions))

		result = get_result(self.pin, self.alice["participant_token"], question.name)
		self.assertTrue(result["is_correct"])
		self.assertGreater(result["points"], 0)
		self.assertEqual(result["rank"], 1)
		self.assertEqual(result["top_5"][0]["nickname"], "alice")

		missed = get_result(self.pin, self.bob["participant_token"], question.name)
		self.assertFalse(missed["answered"])
		self.assertEqual(missed["points"], 0)
		self.assertEqual(missed["rank"], 2)

	def test_podium_survives_reload_after_the_game_ends(self):
		frappe.db.set_value("QZ Session", self.session, "status", "Ended")
		state = get_state(self.pin, self.alice["participant_token"])
		self.assertEqual(state["status"], "Ended")
		self.assertEqual(len(state["leaderboard"]), 2)
