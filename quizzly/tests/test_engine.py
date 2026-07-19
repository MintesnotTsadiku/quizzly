import json
import time
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from quizzly import engine
from quizzly.api import (
	create_session,
	end_session,
	get_state,
	join_session,
	kick_participant,
	submit_answer,
)


class TestScoring(IntegrationTestCase):
	def test_fastest_answer_gets_full_base(self):
		self.assertEqual(engine.compute_points(0, 20000, 1, 1), 1000)

	def test_slowest_answer_gets_half_base(self):
		self.assertEqual(engine.compute_points(20000, 20000, 1, 1), 500)

	def test_grace_overshoot_clamps_to_half_base(self):
		self.assertEqual(engine.compute_points(21000, 20000, 1, 1), 500)

	def test_streak_bonus(self):
		self.assertEqual(engine.compute_points(0, 20000, 2, 1), 1050)

	def test_streak_bonus_caps_at_250(self):
		self.assertEqual(engine.compute_points(0, 20000, 10, 1), 1250)

	def test_multiplier_zero_and_double(self):
		self.assertEqual(engine.compute_points(0, 20000, 1, 0), 0)
		self.assertEqual(engine.compute_points(0, 20000, 1, 2), 2000)


class GameTestCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.quiz = frappe.get_doc(
			{
				"doctype": "QZ Quiz",
				"title": "Engine Quiz",
				"default_time_limit": 20,
				"questions": [
					{
						"question_text": "2 + 2?",
						"option_1": "3",
						"option_2": "4",
						"option_3": "5",
						"option_4": "6",
						"correct_option": "2",
						"time_limit": 1,
					},
					{
						"question_text": "Capital of France?",
						"option_1": "Paris",
						"option_2": "Rome",
						"option_3": "Berlin",
						"option_4": "Madrid",
						"correct_option": "1",
						"time_limit": 1,
						"points_multiplier": "2",
					},
				],
			}
		).insert()
		created = create_session(self.quiz.name)
		self.session = created["session"]
		self.pin = created["game_pin"]
		self.session_doc = frappe.get_doc("QZ Session", self.session)
		self.alice = join_session(self.pin, "alice")
		self.bob = join_session(self.pin, "bob")
		self.questions = frappe.get_doc("QZ Quiz", self.quiz.name).questions

	def tearDown(self):
		engine.clear_state(self.session)
		for question in self.questions:
			frappe.cache.delete_value(engine.answered_key(self.session, question.name))
		frappe.set_user("Administrator")
		super().tearDown()

	def activate(self):
		frappe.db.set_value("QZ Session", self.session, "status", "Active")
		self.session_doc.reload()

	def open_question(self, index=0, window=30):
		question = self.questions[index]
		now = time.time()
		engine.set_state(
			self.session,
			{
				"status": "question",
				"q_index": index,
				"question_row": question.name,
				"opened_at": now,
				"deadline_ts": now + window,
				"window_ms": window * 1000,
				"total": len(self.questions),
			},
			ttl=window + 30,
		)
		return question


class TestSubmitGauntlet(GameTestCase):
	def test_submit_stores_answer_without_correctness_leak(self):
		self.activate()
		question = self.open_question()
		result = submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		self.assertEqual(result, {"ok": True})
		answer = frappe.get_doc(
			"QZ Answer", {"participant": self.alice["participant"], "question_row": question.name}
		)
		self.assertEqual(answer.selected_option, "2")
		self.assertGreaterEqual(answer.response_ms, 0)
		self.assertEqual(answer.points, 0)  # scored only at close

	def test_submit_rejected_when_session_not_active(self):
		question = self.open_question()
		with self.assertRaises(frappe.ValidationError):
			submit_answer(self.pin, self.alice["participant_token"], question.name, "1")

	def test_duplicate_submit_rejected(self):
		self.activate()
		question = self.open_question()
		submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		with self.assertRaises(frappe.ValidationError):
			submit_answer(self.pin, self.alice["participant_token"], question.name, "3")

	def test_db_unique_constraint_is_final_word(self):
		self.activate()
		question = self.open_question()
		submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		# simulate the race: redis pre-check lost, DB constraint must still hold
		frappe.cache.srem(engine.answered_key(self.session, question.name), self.alice["participant"])
		with self.assertRaises(frappe.ValidationError):
			submit_answer(self.pin, self.alice["participant_token"], question.name, "3")

	def test_submit_after_deadline_rejected(self):
		self.activate()
		question = self.open_question()
		state = engine.get_state(self.session)
		state["deadline_ts"] = time.time() - engine.GRACE_SECONDS - 0.1
		engine.set_state(self.session, state, ttl=60)
		with self.assertRaises(frappe.ValidationError):
			submit_answer(self.pin, self.alice["participant_token"], question.name, "2")

	def test_submit_for_non_active_question_rejected(self):
		self.activate()
		self.open_question(index=0)
		other_question = self.questions[1]
		with self.assertRaises(frappe.ValidationError):
			submit_answer(self.pin, self.alice["participant_token"], other_question.name, "1")

	def test_kicked_token_rejected(self):
		self.activate()
		question = self.open_question()
		kick_participant(self.session, self.alice["participant"])
		with self.assertRaises(frappe.PermissionError):
			submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		with self.assertRaises(frappe.PermissionError):
			get_state(self.pin, self.alice["participant_token"])

	def test_question_payload_never_contains_correct_answer(self):
		question = self.questions[0]
		payload = engine.question_payload(self.session_doc, question, 0, 2, time.time() + 20)
		self.assertNotIn("correct", json.dumps(payload))

	def test_get_state_mid_question_gives_remaining_time(self):
		self.activate()
		question = self.open_question(window=30)
		state = get_state(self.pin, self.alice["participant_token"])
		self.assertEqual(state["phase"], "question")
		self.assertFalse(state["answered"])
		self.assertGreater(state["remaining_seconds"], 25)
		self.assertLessEqual(state["remaining_seconds"], 30)
		self.assertNotIn("correct", json.dumps(state["question"]))
		submit_answer(self.pin, self.alice["participant_token"], question.name, "2")
		self.assertTrue(get_state(self.pin, self.alice["participant_token"])["answered"])


class TestGameLoop(GameTestCase):
	def run_loop(self, on_question=None):
		events = []

		def record(event=None, message=None, room=None, **kwargs):
			# frappe internals also publish (doc list_update etc.); keep only our events
			if not isinstance(message, dict) or "type" not in message:
				return
			events.append(message)
			if on_question and message["type"] == "question":
				on_question(message)

		with (
			patch("frappe.publish_realtime", side_effect=record),
			patch("frappe.db.commit"),
			patch.object(engine, "STATS_SECONDS", 0.25),
			patch.object(engine, "GETREADY_SECONDS", 0.25),
			patch.object(engine, "GRACE_SECONDS", 0.25),
			patch.object(engine, "POLL_SECONDS", 0.05),
		):
			engine.run_game_loop(self.session)
		return events

	def submit_scripted_answers(self, message):
		question_row = message["question_row"]
		if message["q_index"] == 0:
			submit_answer(self.pin, self.alice["participant_token"], question_row, "2")
			submit_answer(self.pin, self.bob["participant_token"], question_row, "3")
		else:
			submit_answer(self.pin, self.alice["participant_token"], question_row, "1")

	def test_full_game_to_podium(self):
		self.activate()
		events = self.run_loop(on_question=self.submit_scripted_answers)

		types = [e["type"] for e in events if e["type"] != "answer_count"]
		self.assertEqual(
			types,
			[
				"get_ready",
				"question",
				"question_closed",
				"get_ready",
				"question",
				"question_closed",
				"podium",
			],
		)
		for event in events:
			if event["type"] == "question":
				self.assertNotIn("correct", json.dumps(event))

		first_closed = next(e for e in events if e["type"] == "question_closed")
		self.assertEqual(first_closed["correct_option"], "2")
		self.assertEqual(first_closed["distribution"], {"1": 0, "2": 1, "3": 1, "4": 0})
		self.assertEqual(first_closed["top_5"][0]["nickname"], "alice")

		podium = events[-1]
		self.assertEqual(podium["type"], "podium")
		self.assertEqual([p["nickname"] for p in podium["leaderboard"]], ["alice", "bob"])

		alice = frappe.get_doc("QZ Participant", self.alice["participant"])
		bob = frappe.get_doc("QZ Participant", self.bob["participant"])
		# q1 correct (1x) + q2 correct (2x, streak 2): score > 1500, streak 2
		self.assertGreater(alice.score, 1500)
		self.assertEqual(alice.streak, 2)
		self.assertEqual(alice.rank, 1)
		self.assertEqual(bob.score, 0)
		self.assertEqual(bob.streak, 0)
		self.assertEqual(bob.rank, 2)
		self.assertEqual(frappe.db.get_value("QZ Session", self.session, "status"), "Ended")

	def test_wrong_answer_scores_zero_and_resets_streak(self):
		self.activate()
		question = self.open_question()
		submit_answer(self.pin, self.bob["participant_token"], question.name, "3")
		with patch("frappe.publish_realtime"), patch("frappe.db.commit"):
			engine.close_question(self.session_doc, question, 0, 2)
		bob = frappe.get_doc("QZ Participant", self.bob["participant"])
		self.assertEqual(bob.score, 0)
		self.assertEqual(bob.streak, 0)
		answer = frappe.get_doc(
			"QZ Answer", {"participant": self.bob["participant"], "question_row": question.name}
		)
		self.assertEqual(answer.is_correct, 0)
		self.assertEqual(answer.points, 0)

	def test_skip_control_closes_window_early(self):
		engine.set_control(self.session, "skip")
		started = time.time()
		with patch.object(engine, "POLL_SECONDS", 0.05):
			control = engine.wait_question_window(self.session, deadline_ts=time.time() + 60)
		self.assertEqual(control, "skip")
		self.assertLess(time.time() - started, 2)

	def test_end_session_from_lobby_cancels(self):
		end_session(self.session)
		self.assertEqual(frappe.db.get_value("QZ Session", self.session, "status"), "Cancelled")
