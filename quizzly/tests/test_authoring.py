import frappe
from frappe.client import delete, save
from frappe.tests import IntegrationTestCase

from quizzly import engine
from quizzly.api import create_session, duplicate_quiz, list_quizzes


def question(text="2 + 2?", **overrides) -> dict:
	row = {
		"doctype": "QZ Question",
		"question_text": text,
		"option_1": "3",
		"option_2": "4",
		"option_3": "5",
		"option_4": "6",
		"correct_option": "2",
	}
	row.update(overrides)
	return row


def quiz_doc(questions, base=None) -> dict:
	"""The editor sends back the doc it loaded, with the questions rebuilt in display order."""
	return {**(base or {}), "doctype": "QZ Quiz", "title": "Authored Quiz", "questions": questions}


class TestQuizAuthoring(IntegrationTestCase):
	"""The editor saves through frappe.client.*, so these cover what Quizzly adds to that path:
	the controller's content rules, the question count, and the image on the payload."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_reorder_survives_a_client_save(self):
		saved = save(quiz_doc([question("First"), question("Second"), question("Third")]))

		reordered = save(quiz_doc([question("Third"), question("First")], base=saved))

		rows = frappe.get_all(
			"QZ Question",
			filters={"parent": reordered["name"]},
			fields=["question_text"],
			order_by="idx asc",
		)
		self.assertEqual([row.question_text for row in rows], ["Third", "First"])

	def test_controller_rejects_broken_quizzes(self):
		with self.assertRaises(frappe.ValidationError):
			save(quiz_doc([]))
		with self.assertRaises(frappe.ValidationError):
			save(quiz_doc([question(option_2="  ")]))
		with self.assertRaises(frappe.ValidationError):
			save(quiz_doc([question(correct_option="7")]))

	def test_list_quizzes_counts_questions(self):
		saved = save(quiz_doc([question("First"), question("Second")]))

		listed = next(quiz for quiz in list_quizzes() if quiz["name"] == saved["name"])

		self.assertEqual(listed["question_count"], 2)

	def test_delete_refuses_while_a_session_references_the_quiz(self):
		saved = save(quiz_doc([question()]))
		create_session(saved["name"])

		with self.assertRaises(frappe.LinkExistsError):
			delete("QZ Quiz", saved["name"])

	def test_image_rides_along_on_the_question_payload(self):
		saved = save(quiz_doc([question(image="/files/cat.png"), question("No picture")]))
		session = frappe.get_doc("QZ Session", create_session(saved["name"])["session"])
		questions = engine.get_quiz_questions(session)

		payloads = [engine.question_payload(session, q, 0, 2, 0.0) for q in questions]

		self.assertEqual(payloads[0]["image_url"], "/files/cat.png")
		self.assertIsNone(payloads[1]["image_url"])

	def test_demo_quiz_is_visible_but_read_only_and_can_be_duplicated(self):
		host = frappe.get_doc(
			{
				"doctype": "User",
				"email": "quiz-host-demo@example.com",
				"first_name": "Quiz Host",
				"send_welcome_email": 0,
				"roles": [{"role": "Quiz Host"}],
			}
		).insert(ignore_permissions=True)
		demo = save(
			quiz_doc(
				[question()],
				base={"is_demo": 1, "demo_key": "test-authoring-demo"},
			)
		)
		try:
			frappe.set_user(host.name)
			listed = next(quiz for quiz in list_quizzes() if quiz["name"] == demo["name"])
			self.assertEqual(listed["is_demo"], 1)

			frappe.set_user("Administrator")
			with self.assertRaises(frappe.ValidationError):
				save(quiz_doc([question("Changed")], base=demo))

			copied_name = duplicate_quiz(demo["name"])["name"]
			copied = frappe.get_doc("QZ Quiz", copied_name)
			self.assertEqual(copied.is_demo, 0)
			self.assertIsNone(copied.demo_key)
			frappe.delete_doc("QZ Quiz", copied.name, force=True, ignore_permissions=True)
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_value("QZ Quiz", demo["name"], "is_demo", 0)
			frappe.delete_doc("QZ Quiz", demo["name"], force=True, ignore_permissions=True)
			frappe.delete_doc("User", host.name, force=True, ignore_permissions=True)
