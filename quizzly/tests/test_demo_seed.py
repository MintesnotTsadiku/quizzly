import json

from frappe.tests import UnitTestCase

from quizzly.demo.seed import demo_files


class TestQuizDemoCatalog(UnitTestCase):
	def test_quiz_ships_three_complete_demo_sets(self):
		files = demo_files("quiz")
		self.assertEqual(len(files), 3)

		catalog = [json.loads(path.read_text()) for path in files]
		self.assertEqual(len({item["demo_key"] for item in catalog}), 3)
		for quiz in catalog:
			self.assertEqual(quiz["game_key"], "quiz")
			self.assertGreaterEqual(len(quiz["questions"]), 10)
			for question in quiz["questions"]:
				self.assertIn(question["correct_option"], {"1", "2", "3", "4"})
				self.assertTrue(question.get("explanation"))
				for index in range(1, 5):
					self.assertTrue(question.get(f"option_{index}"))
