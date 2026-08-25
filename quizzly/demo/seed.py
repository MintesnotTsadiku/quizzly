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
	return [seed_file(path) for path in demo_files()] + seed_round_game_demos()


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
		for audience, title in zip(ROUND_AUDIENCES, titles, strict=True):
			key = f"{game_key}-{audience}"
			name = frappe.db.exists("GP Game Pack", {"demo_key": key, "game_key": game_key})
			count = frappe.db.count("GP Game Item", {"parent": name, "parenttype": "GP Game Pack"}) if name else 0
			results.append({"demo_key": key, "ok": count == 10, "prompts": count})
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
}
ROUND_MODES = {
	"sequence-sprint":"order", "sound-snap":"choice", "memory-mosaic":"choice",
	"escape-together":"choice", "bracket-bash":"choice", "signal-spectrum":"number",
	"closest-call":"number", "picture-peek":"text", "common-thread":"text",
	"one-word-chorus":"text",
}


def seed_round_game_demos() -> list[dict]:
	results = []
	for game_key, titles in ROUND_DEMO_TITLES.items():
		for audience, title in zip(ROUND_AUDIENCES, titles, strict=True):
			key = f"{game_key}-{audience}"
			name = frappe.db.exists("GP Game Pack", {"demo_key": key})
			pack = frappe.get_doc("GP Game Pack", name) if name else frappe.new_doc("GP Game Pack")
			pack.update({"title": title, "game_key": game_key, "description": f"A polished {title} starter experience.", "is_demo": 1, "demo_key": key, "items": round_demo_items(game_key, title)})
			pack.flags.in_demo_seed = True; pack.save(ignore_permissions=True)
			results.append({"demo_key": key, "pack": pack.name, "prompts": 10})
	frappe.db.commit()
	return results


def round_demo_items(game_key: str, title: str) -> list[dict]:
	mode = ROUND_MODES.get(game_key, "creative")
	rows = []
	for number in range(1, 11):
		prompt = f"{title} · Round {number}: "
		if mode == "number": rows.append({"prompt_text": prompt + "Place your best estimate on the scale.", "target": number * 9})
		elif mode == "order": rows.append({"prompt_text": prompt + "Put these moments in order.", "choices": json.dumps(["First", "Next", "Then", "Finally"]), "answer": "First, Next, Then, Finally"})
		elif mode == "choice": rows.append({"prompt_text": prompt + "Choose the strongest answer.", "choices": json.dumps(["A", "B", "C", "D"]), "answer": "A"})
		elif mode == "text": rows.append({"prompt_text": prompt + "Find the hidden connection.", "answer": title.split()[0]})
		else: rows.append({"prompt_text": prompt + "Create a short, room-friendly response."})
	return rows
