import json

import frappe
from frappe.tests import IntegrationTestCase

from quizzly import engine
from quizzly.api import create_session, delete_quiz, get_quiz, list_quizzes, save_quiz


def question(text="2 + 2?", **overrides) -> dict:
	row = {
		"question_text": text,
		"option_1": "3",
		"option_2": "4",
		"option_3": "5",
		"option_4": "6",
		"correct_option": "2",
	}
	row.update(overrides)
	return row


class TestQuizAuthoring(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def save(self, questions, quiz=None, title="Authored Quiz"):
		return save_quiz(title=title, questions=json.dumps(questions), quiz=quiz)["quiz"]

	def test_create_reorder_and_delete_rows(self):
		name = self.save([question("First"), question("Second"), question("Third")])

		loaded = get_quiz(name)
		self.assertEqual([row["question_text"] for row in loaded["questions"]], ["First", "Second", "Third"])
		self.assertIn(name, [quiz["name"] for quiz in list_quizzes()])
		self.assertEqual(next(q for q in list_quizzes() if q["name"] == name)["question_count"], 3)

		self.save([question("Third"), question("First")], quiz=name)

		rows = frappe.get_all(
			"QZ Question", filters={"parent": name}, fields=["question_text"], order_by="idx asc"
		)
		self.assertEqual([row.question_text for row in rows], ["Third", "First"])

	def test_validation_rejects_broken_quizzes(self):
		with self.assertRaises(frappe.ValidationError):
			self.save([])
		with self.assertRaises(frappe.ValidationError):
			self.save([question(option_2="  ")])
		with self.assertRaises(frappe.ValidationError):
			self.save([question(correct_option="7")])
		with self.assertRaises(frappe.ValidationError):
			self.save([question(time_limit=300)])

	def test_delete_refuses_while_a_session_references_the_quiz(self):
		name = self.save([question()])
		create_session(name)

		with self.assertRaises(frappe.ValidationError):
			delete_quiz(name)

	def test_delete_removes_an_unplayed_quiz(self):
		name = self.save([question()])
		delete_quiz(name)

		self.assertFalse(frappe.db.exists("QZ Quiz", name))

	def test_image_rides_along_on_the_question_payload(self):
		name = self.save([question(image="/files/cat.png"), question("No picture")])
		session = frappe.get_doc("QZ Session", create_session(name)["session"])
		questions = engine.get_quiz_questions(session)

		payloads = [engine.question_payload(session, q, 0, 2, 0.0) for q in questions]

		self.assertEqual(payloads[0]["image_url"], "/files/cat.png")
		self.assertIsNone(payloads[1]["image_url"])
