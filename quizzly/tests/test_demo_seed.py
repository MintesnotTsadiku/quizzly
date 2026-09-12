import json

from frappe.tests import UnitTestCase

from quizzly.demo.seed import demo_files


class TestQuizDemoCatalog(UnitTestCase):
	def test_quiz_ships_composed_and_funny_demo_sets(self):
		files = demo_files("quiz")
		self.assertEqual(len(files), 7)

		catalog = {item["demo_key"]: item for item in (json.loads(path.read_text()) for path in files)}
		self.assertEqual(
			set(catalog),
			{
				"quiz-church-bible",
				"quiz-family-general",
				"quiz-big-room",
				"quiz-funny",
				"quiz-amharic-riddles-1",
				"quiz-amharic-riddles-2",
				"quiz-amharic-riddles-3",
			},
		)
		for demo_key, expected in {
			"quiz-church-bible": 30,
			"quiz-family-general": 30,
			"quiz-big-room": 30,
			"quiz-funny": 20,
			"quiz-amharic-riddles-1": 15,
			"quiz-amharic-riddles-2": 15,
			"quiz-amharic-riddles-3": 15,
		}.items():
			quiz = catalog[demo_key]
			self.assertEqual(quiz["game_key"], "quiz")
			self.assertEqual(len(quiz["questions"]), expected)
			for index, question in enumerate(quiz["questions"]):
				self.assertIn(question["correct_option"], {"1", "2", "3", "4"})
				self.assertTrue(question.get("explanation"))
				for option in range(1, 5):
					self.assertTrue(question.get(f"option_{option}"))
				if demo_key.startswith("quiz-amharic-riddles-"):
					self.assertTrue(question["question_text"].startswith(f"{index + 1} — "))
				elif demo_key != "quiz-funny":
					part = "Part 1" if index % 2 == 0 else "Part 2"
					self.assertIn(part, question["question_text"])
					self.assertEqual(question["points_multiplier"], "1" if index % 2 == 0 else "2")
