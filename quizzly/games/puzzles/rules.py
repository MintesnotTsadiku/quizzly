"""Pure, authoritative rules for five distinct room puzzles.

All input is validated here, independent of the transport and presentation.
"""

from copy import deepcopy

KEYS = {"dots-and-boxes", "group-sudoku", "path-weaver", "hidden-picture", "quilt-puzzle"}


def initial(key):
	base = {"game": key, "done": False, "moves": 0}
	if key == "dots-and-boxes":
		base.update(edges={}, boxes={}, turn="X", scores={"X": 0, "O": 0}, side_moves={"X": 0, "O": 0})
	elif key == "group-sudoku":
		base.update(
			cells=[1, 0, 0, 4, 0, 4, 1, 0, 0, 1, 4, 0, 4, 0, 0, 1],
			notes={},
			givens=[0, 3, 5, 6, 9, 10, 12, 15],
		)
	elif key == "path-weaver":
		base.update(size=5, path=[0], blocked=[6, 7, 16, 18], checkpoints=[4, 12, 20], exit=24)
	elif key == "hidden-picture":
		base.update(
			size=5, cells=[0] * 25, rows=[[1, 1], [5], [5], [3], [1]], columns=[[2], [4], [4], [4], [2]]
		)
	elif key == "quilt-puzzle":
		base.update(
			size=4,
			pieces=[
				[[0, 0], [1, 0], [2, 0], [3, 0]],
				[[0, 0], [0, 1], [0, 2], [1, 2]],
				[[0, 0], [1, 0], [2, 0], [0, 1]],
				[[0, 0], [1, 0], [0, 1], [1, 1]],
			],
			placements={},
		)
	else:
		raise ValueError("Unknown puzzle")
	return base


def index(value, size):
	if type(value) is not int or not 0 <= value < size:
		raise ValueError("Choose a cell on the board.")
	return value


def runs(values):
	result = []
	for v in values:
		if v:
			if not result or result[-1] == 0:
				result.append(1)
			else:
				result[-1] += 1
		elif result and result[-1]:
			result.append(0)
	return [v for v in result if v]


def apply(current, action, payload):
	if current["done"]:
		raise ValueError("This puzzle is complete.")
	s = deepcopy(current)
	key = s["game"]
	if key == "dots-and-boxes":
		if action != "edge":
			raise ValueError("Choose an edge.")
		edge = payload.get("edge", "")
		allowed = {f"h:{r}:{c}" for r in range(4) for c in range(3)} | {
			f"v:{r}:{c}" for r in range(3) for c in range(4)
		}
		if not isinstance(edge, str) or edge not in allowed or edge in s["edges"]:
			raise ValueError("Choose an empty edge.")
		s["edges"][edge] = s["turn"]
		gained = 0
		for r in range(3):
			for c in range(3):
				box = f"{r}:{c}"
				if box not in s["boxes"] and all(
					e in s["edges"] for e in (f"h:{r}:{c}", f"h:{r + 1}:{c}", f"v:{r}:{c}", f"v:{r}:{c + 1}")
				):
					s["boxes"][box] = s["turn"]
					gained += 1
		s["scores"][s["turn"]] += gained
		s["side_moves"][s["turn"]] += 1
		if not gained:
			s["turn"] = "O" if s["turn"] == "X" else "X"
		s["done"] = len(s["boxes"]) == 9
	elif key == "group-sudoku":
		cell = index(payload.get("cell"), 16)
		value = index(payload.get("value"), 5)
		if cell in s["givens"]:
			raise ValueError("A given cannot be changed.")
		if action == "note":
			if not value:
				s["notes"].pop(str(cell), None)
			else:
				notes = s["notes"].setdefault(str(cell), [])
				notes.remove(value) if value in notes else notes.append(value)
		elif action == "cell":
			row, col = divmod(cell, 4)
			peers = (
				{row * 4 + c for c in range(4)}
				| {r * 4 + col for r in range(4)}
				| {(row // 2 * 2 + r) * 4 + col // 2 * 2 + c for r in range(2) for c in range(2)}
			)
			if value and any(s["cells"][p] == value for p in peers - {cell}):
				raise ValueError("That number already appears in this row, column or region.")
			s["cells"][cell] = value
			s["notes"].pop(str(cell), None)
			s["done"] = all(s["cells"])
		else:
			raise ValueError("Choose a number or note.")
	elif key == "path-weaver":
		if action == "undo":
			if len(s["path"]) > 1:
				s["path"].pop()
		elif action == "cell":
			cell = index(payload.get("cell"), 25)
			last = s["path"][-1]
			if (
				cell in s["blocked"]
				or cell in s["path"]
				or abs(cell // 5 - last // 5) + abs(cell % 5 - last % 5) != 1
			):
				raise ValueError("Choose an unused neighboring cell.")
			if cell == s["exit"] and not set(s["checkpoints"]).issubset(s["path"]):
				raise ValueError("Visit every star before the exit.")
			s["path"].append(cell)
			s["done"] = cell == s["exit"]
		else:
			raise ValueError("Extend or undo the path.")
	elif key == "hidden-picture":
		if action != "cell":
			raise ValueError("Mark a cell.")
		cell = index(payload.get("cell"), 25)
		value = index(payload.get("value"), 3)
		s["cells"][cell] = value
		s["done"] = all(
			runs([s["cells"][r * 5 + c] == 1 for c in range(5)]) == s["rows"][r] for r in range(5)
		) and all(runs([s["cells"][r * 5 + c] == 1 for r in range(5)]) == s["columns"][c] for c in range(5))
	elif key == "quilt-puzzle":
		piece = index(payload.get("piece"), len(s["pieces"]))
		if action == "remove":
			s["placements"].pop(str(piece), None)
		elif action == "place":
			cell = index(payload.get("cell"), 16)
			rotation = index(payload.get("rotation", 0), 4)
			points = s["pieces"][piece]
			for _ in range(rotation):
				points = [[-y, x] for x, y in points]
			minx = min(x for x, y in points)
			miny = min(y for x, y in points)
			coords = [(cell % 4 + x - minx, cell // 4 + y - miny) for x, y in points]
			if any(x >= 4 or y >= 4 for x, y in coords):
				raise ValueError("Keep the whole patch inside the quilt.")
			occupied = {v for k, p in s["placements"].items() if k != str(piece) for v in p}
			cells = [y * 4 + x for x, y in coords]
			if occupied.intersection(cells):
				raise ValueError("Patches cannot overlap.")
			s["placements"][str(piece)] = cells
			s["done"] = sum(len(p) for p in s["placements"].values()) == 16
		else:
			raise ValueError("Place or remove a patch.")
	s["moves"] += 1
	return s
