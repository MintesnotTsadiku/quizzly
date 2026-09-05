import unittest

from quizzly.games.puzzles.rules import apply, initial
from quizzly.games.round_games.game import RoundGame


class PuzzleRules(unittest.TestCase):
	def test_unicode_and_symbols_remain_distinct(self):
		norm = RoundGame().norm
		self.assertNotEqual(norm("ድመት"), norm("ውሻ"))
		self.assertNotEqual(norm("■■■··"), norm("■·■■·"))
		self.assertEqual(norm(" CAFÉ "), norm("cafe\u0301"))
		self.assertEqual(norm(0), "0")

	def test_dots_extra_turn_and_completion(self):
		s = initial("dots-and-boxes")
		for edge in ["h:0:0", "h:1:0", "v:0:0"]:
			s = apply(s, "edge", {"edge": edge})
		turn = s["turn"]
		s = apply(s, "edge", {"edge": "v:0:1"})
		self.assertEqual(s["turn"], turn)
		self.assertEqual(s["scores"][turn], 1)
		with self.assertRaises(ValueError):
			apply(s, "edge", {"edge": "v:0:1"})
		for edge in [f"h:{r}:{c}" for r in range(4) for c in range(3)] + [
			f"v:{r}:{c}" for r in range(3) for c in range(4)
		]:
			if edge not in s["edges"]:
				s = apply(s, "edge", {"edge": edge})
		self.assertTrue(s["done"])
		self.assertEqual(sum(s["scores"].values()), 9)

	def test_sudoku_givens_conflicts_notes_and_solution(self):
		s = initial("group-sudoku")
		with self.assertRaises(ValueError):
			apply(s, "cell", {"cell": 0, "value": 2})
		with self.assertRaises(ValueError):
			apply(s, "cell", {"cell": 1, "value": 1})
		s = apply(s, "note", {"cell": 1, "value": 2})
		self.assertEqual(s["notes"]["1"], [2])
		solution = [1, 2, 3, 4, 3, 4, 1, 2, 2, 1, 4, 3, 4, 3, 2, 1]
		for i, v in enumerate(solution):
			if i not in s["givens"]:
				s = apply(s, "cell", {"cell": i, "value": v})
		self.assertTrue(s["done"])

	def test_path_solution_undo_and_invalid_jump(self):
		s = initial("path-weaver")
		with self.assertRaises(ValueError):
			apply(s, "cell", {"cell": 4})
		s = apply(s, "cell", {"cell": 1})
		s = apply(s, "undo", {})
		self.assertEqual(s["path"], [0])
		# The room can route around the walls, through all three stars.

		# Search proves the authored puzzle is solvable under the actual rules.
		def solve(s):
			if s["done"]:
				return s
			for i in range(25):
				try:
					n = apply(s, "cell", {"cell": i})
				except ValueError:
					continue
				result = solve(n)
				if result:
					return result

		self.assertTrue(solve(s)["done"])

	def test_nonogram_solution(self):
		s = initial("hidden-picture")
		picture = ["01010", "11111", "11111", "01110", "00100"]
		for r, row in enumerate(picture):
			for c, v in enumerate(row):
				if v == "1":
					s = apply(s, "cell", {"cell": r * 5 + c, "value": 1})
		self.assertTrue(s["done"])

	def test_quilt_bounds_overlap_completion(self):
		s = initial("quilt-puzzle")
		with self.assertRaises(ValueError):
			apply(s, "place", {"piece": 0, "cell": 15})
		s = apply(s, "place", {"piece": 0, "cell": 0})
		with self.assertRaises(ValueError):
			apply(s, "place", {"piece": 1, "cell": 0})
		for piece, cell in [(1, 4), (2, 5), (3, 10)]:
			s = apply(s, "place", {"piece": piece, "cell": cell})
		self.assertTrue(s["done"])
