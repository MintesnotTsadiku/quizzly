"""GatherPlay demo content: idempotent seeding and verification.

Every implemented module ships three starter experiences (church/Bible, child/family,
general assembly). Demos carry a stable ``demo_key`` so repeated seeds upsert instead
of duplicating, hosts can duplicate a demo to customize it, and reseeding never touches
host-created content.
"""

import json
from pathlib import Path

import frappe

DEMO_DIR = Path(frappe.get_app_path("quizzly")) / "demo_data"

# game_key -> (pack doctype, prompt doctype, prompt field mapper)
CONTENT = {
	"cuecast": ("GP Cue Deck", "GP Cue Prompt", lambda item: {"prompt_text": item}),
	"crowd-compass": (
		"GP Crowd Pack",
		"GP Crowd Prompt",
		lambda item: {
			"prompt_text": item["prompt"],
			**{f"choice_{i + 1}": choice for i, choice in enumerate(item["choices"])},
		},
	),
	"doodle-dash": (
		"GP Draw Pack",
		"GP Draw Prompt",
		lambda item: {
			"prompt_text": item["prompt"] if isinstance(item, dict) else item,
			"aliases": ", ".join(item.get("aliases") or []) if isinstance(item, dict) else "",
		},
	),
}


def demo_files(game_key: str | None = None) -> list[Path]:
	pattern = f"{game_key}/*.json" if game_key else "*/*.json"
	return sorted(DEMO_DIR.glob(pattern))


def seed_all() -> list[dict]:
	results = [seed_file(path) for path in demo_files()] + seed_round_game_demos()
	from quizzly.demo.curated import seed_curated_starters

	seed_curated_starters()
	return results


def seed_file(path: Path) -> dict:
	data = json.loads(path.read_text())
	pack = upsert(data)
	items = pack.questions if data["game_key"] == "quiz" else pack.prompts
	return {"demo_key": data["demo_key"], "pack": pack.name, "prompts": len(items or [])}


def upsert(data: dict):
	game_key = data["game_key"]
	if game_key == "quiz":
		return upsert_quiz(data)
	pack_doctype, _prompt_doctype, to_row = CONTENT[game_key]
	existing = data["demo_key"] and frappe.db.exists(pack_doctype, {"demo_key": data["demo_key"]})
	if existing:
		pack = frappe.get_doc(pack_doctype, existing)
	else:
		pack = frappe.new_doc(pack_doctype)
	pack.update(
		{
			"title": data["title"],
			"is_demo": 1,
			"demo_key": data["demo_key"],
			"prompts": [to_row(item) for item in data["prompts"]],
		}
	)
	if game_key == "crowd-compass":
		pack.ranked = int(data.get("ranked") or 0)
	elif game_key == "cuecast":
		pack.mode = data.get("mode") or "Act"
	elif game_key == "doodle-dash":
		pack.description = data.get("description")
	pack.flags.in_demo_seed = True
	pack.save(ignore_permissions=True)
	frappe.db.commit()
	return pack


def upsert_quiz(data: dict):
	name = frappe.db.exists("QZ Quiz", {"demo_key": data["demo_key"]})
	quiz = frappe.get_doc("QZ Quiz", name) if name else frappe.new_doc("QZ Quiz")
	quiz.update(
		{
			"title": data["title"],
			"description": data.get("description"),
			"default_time_limit": data.get("default_time_limit") or 20,
			"show_explanation": int(data.get("show_explanation", 1)),
			"explanation_position": data.get("explanation_position") or "Before Stats",
			"explanation_time_limit": data.get("explanation_time_limit") or 10,
			"is_demo": 1,
			"demo_key": data["demo_key"],
			"questions": data["questions"],
		}
	)
	if data.get("content_language"):
		quiz.content_language = data["content_language"]
	quiz.flags.in_demo_seed = True
	quiz.save(ignore_permissions=True)
	frappe.db.commit()
	return quiz


def verify_all() -> list[dict]:
	"""Confirm every shipped demo exists with its expected prompt count."""
	results = []
	for path in demo_files():
		data = json.loads(path.read_text())
		if data["game_key"] == "quiz":
			pack_doctype, prompt_doctype = "QZ Quiz", "QZ Question"
		else:
			pack_doctype, prompt_doctype = CONTENT[data["game_key"]][:2]
		name = frappe.db.exists(pack_doctype, {"demo_key": data["demo_key"]})
		ok = bool(name)
		count = 0
		if ok:
			count = frappe.db.count(prompt_doctype, {"parent": name, "parenttype": pack_doctype})
			expected = data.get("questions") or data.get("prompts") or []
			ok = count >= len(expected)
		results.append({"demo_key": data["demo_key"], "ok": ok, "prompts": count})
	for game_key, titles in ROUND_DEMO_TITLES.items():
		for audience, _title in zip(ROUND_AUDIENCES, titles, strict=True):
			key = f"{game_key}-{audience}"
			name = frappe.db.exists("GP Game Pack", {"demo_key": key, "game_key": game_key})
			count = (
				frappe.db.count("GP Game Item", {"parent": name, "parenttype": "GP Game Pack"}) if name else 0
			)
			results.append({"demo_key": key, "ok": count == ROUND_COUNTS.get(game_key, 10), "prompts": count})
	return results


def hide_all() -> None:
	"""Demos stay playable but disappear from the catalog when a site opts out."""
	for pack_doctype in {definition[0] for definition in CONTENT.values()}:
		for name in frappe.get_all(pack_doctype, filters={"is_demo": 1}, pluck="name"):
			frappe.db.set_value(pack_doctype, name, "is_demo", 0)
	for name in frappe.get_all("QZ Quiz", filters={"is_demo": 1}, pluck="name"):
		frappe.db.set_value("QZ Quiz", name, "is_demo", 0)


ROUND_AUDIENCES = ("church-bible", "family-general", "big-room")
ROUND_DEMO_TITLES = {
	"bluffline": ("Curious Bible Context", "Silly Word Museum", "Unexpected Facts"),
	"sequence-sprint": ("Bible Timeline Relay", "Put It in Order", "Process and History Race"),
	"picture-peek": ("Symbols, Places, and Scenes", "What Is Hiding?", "World in Focus"),
	"sound-snap": ("Sounds of the Story", "Home and Animal Sounds", "Soundscape Challenge"),
	"caption-clash": ("Modern Parable Moments", "Family Photo Giggles", "Conference Caption Cup"),
	"story-loom": ("Journey of Courage", "The Bedtime Adventure Machine", "Fifty Voices, One City"),
	"signal-spectrum": ("Journey and Wisdom Scales", "Silly Family Scales", "Know Your Room"),
	"memory-mosaic": ("Objects and Journeys Memory", "Toy Room Memory", "Auditorium Snapshot"),
	"common-thread": ("Threads Through Scripture", "Family Connection Box", "Big Room Connections"),
	"escape-together": ("The Lamp and the Locked Library", "The Friendly Castle Escape", "The Assembly Code"),
	"bracket-bash": ("Bible Story Bracket", "Family Favorites Cup", "Big Room Championship"),
	"closest-call": ("Bible Numbers Duel", "Family Guess-Off", "Assembly Estimation Arena"),
	"phrase-forge": ("Words of Encouragement", "Silly Sentence Factory", "Conference Phrase Forge"),
	"seek-and-show": ("Service and Symbols Hunt", "Home or Hall Treasure Hunt", "Venue Team Quest"),
	"one-word-chorus": ("People, Places, and Symbols", "Animals and Everyday Things", "One Word, Big Room"),
	"grid-conquest": ("Connect the Story", "Family Grid Conquest", "Big Room Grid Battle"),
	"dots-and-boxes": ("Community Squares", "Family Box Builders", "Assembly Territory"),
	"hidden-picture": ("Symbols Revealed", "Family Hidden Pictures", "Big Screen Pixel Reveal"),
	"path-weaver": ("Journey Paths", "Family Path Weaver", "Assembly Route Challenge"),
	"quilt-puzzle": ("Patterns and Places", "Family Quilt Puzzle", "Big Room Pattern Lab"),
	"group-sudoku": ("Symbol Sudoku", "Family Mini Sudoku", "Assembly Logic Grid"),
}
ROUND_MODES = {
	"sequence-sprint": "order",
	"sound-snap": "choice",
	"memory-mosaic": "choice",
	"escape-together": "choice",
	"bracket-bash": "choice",
	"signal-spectrum": "number",
	"closest-call": "number",
	"picture-peek": "text",
	"common-thread": "text",
	"one-word-chorus": "text",
	"phrase-forge": "order",
	"grid-conquest": "choice",
	"dots-and-boxes": "choice",
	"hidden-picture": "choice",
	"path-weaver": "choice",
	"quilt-puzzle": "choice",
	"group-sudoku": "choice",
}
ROUND_COUNTS = {
	"bluffline": 12,
	"caption-clash": 12,
	"picture-peek": 12,
	"sound-snap": 12,
	"memory-mosaic": 12,
	"closest-call": 12,
	"common-thread": 24,
	"one-word-chorus": 24,
	"escape-together": 6,
	"bracket-bash": 8,
	"grid-conquest": 4,
	"dots-and-boxes": 4,
	"hidden-picture": 4,
	"path-weaver": 4,
	"quilt-puzzle": 4,
	"group-sudoku": 4,
}
AUDIENCE_TOPICS = {
	"church-bible": [
		"welcome",
		"lamp",
		"journey",
		"shepherd",
		"scroll",
		"boat",
		"courage",
		"service",
		"wisdom",
		"community",
		"hope",
		"celebration",
	],
	"family-general": [
		"rainbow",
		"picnic",
		"robot",
		"garden",
		"bicycle",
		"puzzle",
		"kindness",
		"breakfast",
		"library",
		"playground",
		"music",
		"adventure",
	],
	"big-room": [
		"arrival",
		"stage",
		"workshop",
		"coffee break",
		"teamwork",
		"travel",
		"innovation",
		"city",
		"microphone",
		"celebration",
		"conference",
		"connection",
	],
}


def seed_round_game_demos() -> list[dict]:
	results = []
	for game_key, titles in ROUND_DEMO_TITLES.items():
		for audience, title in zip(ROUND_AUDIENCES, titles, strict=True):
			key = f"{game_key}-{audience}"
			name = frappe.db.exists("GP Game Pack", {"demo_key": key})
			pack = frappe.get_doc("GP Game Pack", name) if name else frappe.new_doc("GP Game Pack")
			pack.update(
				{
					"title": title,
					"game_key": game_key,
					"description": f"A ready-to-host {title} experience with clear, room-safe prompts and a five-minute preview path.",
					"is_demo": 1,
					"demo_key": key,
					"items": round_demo_items(game_key, title, audience),
				}
			)
			pack.flags.in_demo_seed = True
			pack.save(ignore_permissions=True)
			results.append({"demo_key": key, "pack": pack.name, "prompts": ROUND_COUNTS.get(game_key, 10)})
	frappe.db.commit()
	return results


def round_demo_items(game_key: str, title: str, audience: str) -> list[dict]:
	mode = ROUND_MODES.get(game_key, "creative")
	rows = []
	topics = AUDIENCE_TOPICS[audience]
	for number in range(1, ROUND_COUNTS.get(game_key, 10) + 1):
		topic = topics[(number - 1) % len(topics)]
		prompt = f"{title} · {number}. "
		if mode == "number":
			rows.append(
				{
					"prompt_text": prompt
					+ f"Where should '{topic}' land from 0 to 100? Lock one shared estimate.",
					"target": 8 + ((number * 17) % 85),
					"answer": "Reveal the target and compare the distance.",
				}
			)
		elif mode == "order":
			cards = [f"Notice {topic}", "Choose the next step", "Act together", "Check the result"]
			rows.append(
				{
					"prompt_text": prompt + f"Rebuild the {topic} sequence.",
					"choices": json.dumps(cards),
					"answer": " → ".join(cards),
				}
			)
		elif mode == "choice":
			puzzle = _puzzle_choice(game_key, number)
			if puzzle:
				rows.append({"prompt_text": prompt + puzzle[0], "choices": json.dumps(puzzle[1]), "answer": puzzle[2]})
				continue
			choices = [f"Observe {topic}", "Ask for a clue", "Work as a team", "Check every detail"]
			rows.append(
				{
					"prompt_text": prompt + f"Which clue best completes this {topic} challenge?",
					"choices": json.dumps(choices),
					"answer": choices[number % len(choices)],
				}
			)
		elif mode == "text":
			rows.append(
				{
					"prompt_text": prompt
					+ f"The clues point toward {topic}. Name the common thread as early as you can.",
					"answer": topic,
				}
			)
		else:
			verb = {
				"bluffline": "Write a believable false definition",
				"caption-clash": "Write one warm, surprising caption",
				"story-loom": "Continue the shared story in one vivid sentence",
				"seek-and-show": "Describe the safe object or team creation you found",
			}.get(game_key, "Create one concise clue")
			rows.append({"prompt_text": prompt + f"{verb} inspired by '{topic}'.", "answer": topic})
	return rows


def _puzzle_choice(game_key: str, number: int):
	"""Small simultaneous puzzles keep every person active in rooms of 4-100."""
	variants = {
		"grid-conquest": [
			("X X · / O O · / · · · — where should X play to complete the top row?", ["Top right", "Middle right", "Bottom left", "Centre"], "Top right"),
			("X O · / X O · / · · · — where should X play to complete the left column?", ["Bottom left", "Top right", "Bottom right", "Centre"], "Bottom left"),
			("X O · / O X · / · · · — where should X play to complete the diagonal?", ["Bottom right", "Top right", "Bottom left", "Middle right"], "Bottom right"),
			("O O · / X · · / X · · — where must X play to block O's top row?", ["Top right", "Centre", "Bottom right", "Middle right"], "Top right"),
		],
		"dots-and-boxes": [
			("The highlighted box already has TOP, LEFT, and BOTTOM. Which missing edge claims it?", ["Top edge", "Right edge", "Bottom edge", "Left edge"], "Right edge"),
			("The highlighted box already has TOP, RIGHT, and BOTTOM. Which missing edge claims it?", ["Left edge", "Right edge", "Bottom edge", "Top edge"], "Left edge"),
			("The highlighted box already has LEFT, RIGHT, and BOTTOM. Which missing edge claims it?", ["Top edge", "Right edge", "Bottom edge", "Left edge"], "Top edge"),
			("The highlighted box already has TOP, LEFT, and RIGHT. Which missing edge claims it?", ["Bottom edge", "Right edge", "Top edge", "Left edge"], "Bottom edge"),
		],
		"hidden-picture": [
			("Row clue 3: which candidate has exactly one uninterrupted group of three filled cells?", ["■■■··", "■·■■·", "■■·■■", "·■·■·"], "■■■··"),
			("Row clue 1,1: which candidate has two single filled cells separated by a gap?", ["■·■··", "■■···", "·■■··", "■■■··"], "■·■··"),
			("Row clue 2: which candidate has exactly one uninterrupted group of two filled cells?", ["·■■··", "■·■··", "■■■··", "■·■■·"], "·■■··"),
			("Row clue 2,1: which candidate has a pair followed later by one single filled cell?", ["■■·■·", "■■■··", "■·■■·", "·■■■·"], "■■·■·"),
		],
		"path-weaver": [
			("Ahead is blocked, LEFT revisits a cell, RIGHT is open, and STOP misses the exit. Which move stays legal?", ["Turn left", "Turn right", "Continue straight", "Stop"], "Turn right"),
			("RIGHT is blocked, STRAIGHT revisits a cell, LEFT is open toward the exit, and STOP is early. Choose the legal move.", ["Turn left", "Turn right", "Continue straight", "Stop"], "Turn left"),
			("LEFT and RIGHT are blocked, STRAIGHT is open toward the checkpoint, and STOP is early. Choose the legal move.", ["Continue straight", "Turn right", "Turn left", "Stop"], "Continue straight"),
			("The route has reached the exit; every movement option leaves the board. What is the valid action?", ["Stop", "Turn right", "Continue straight", "Turn left"], "Stop"),
		],
		"quilt-puzzle": [
			("Complete the repeating pattern: circle, square, circle, square, ___.", ["Circle", "Square", "Triangle", "Diamond"], "Circle"),
			("Complete the repeating pattern: triangle, triangle, diamond, triangle, triangle, ___.", ["Diamond", "Triangle", "Circle", "Square"], "Diamond"),
			("Complete the repeating pattern: red, blue, green, red, blue, ___.", ["Green", "Red", "Blue", "Yellow"], "Green"),
			("Complete the growing pattern: one dot, two dots, three dots, ___.", ["Four dots", "Two dots", "Five dots", "One dot"], "Four dots"),
		],
		"group-sudoku": [
			("4×4 Sudoku: target row is 1, 2, _, 4; its column has 1, 2, 4. Which value fits?", ["1", "2", "3", "4"], "3"),  # noqa: RUF001 - mathematical dimensions in existing content
			("4×4 Sudoku: target row is 4, _, 2, 1; its column has 1, 2, 4. Which value fits?", ["3", "1", "2", "4"], "3"),  # noqa: RUF001 - mathematical dimensions in existing content
			("4×4 Sudoku: target row is _, 1, 4, 3; its column has 1, 3, 4. Which value fits?", ["2", "1", "3", "4"], "2"),  # noqa: RUF001 - mathematical dimensions in existing content
			("4×4 Sudoku: target row is 3, 4, 1, _; its column has 1, 3, 4. Which value fits?", ["2", "4", "1", "3"], "2"),  # noqa: RUF001 - mathematical dimensions in existing content
		],
	}
	game_variants = variants.get(game_key)
	if not game_variants:
		return None
	base = game_variants[(number - 1) % len(game_variants)]
	prompt, choices, answer = base
	return prompt, choices, answer
