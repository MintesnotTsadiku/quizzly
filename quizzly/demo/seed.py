"""GatherPlay demo content: idempotent seeding and verification.

Every implemented module ships three starter experiences (church/Bible, child/family,
general assembly). Demos carry a stable ``demo_key`` so repeated seeds upsert instead
of duplicating, hosts can duplicate a demo to customize it, and reseeding never touches
host-created decks.
"""

import json
from pathlib import Path

import frappe

DEMO_DIR = Path(frappe.get_app_path("quizzly")) / "demo_data"


def demo_files(game_key: str | None = None) -> list[Path]:
	pattern = f"{game_key}/*.json" if game_key else "*/*.json"
	return sorted(DEMO_DIR.glob(pattern))


def seed_all() -> list[dict]:
	return [seed_file(path) for path in demo_files()]


def seed_file(path: Path) -> dict:
	data = json.loads(path.read_text())
	deck = upsert_deck(data)
	return {"demo_key": data["demo_key"], "deck": deck.name, "prompts": len(deck.prompts or [])}


def upsert_deck(data: dict) -> object:
	existing = data["demo_key"] and frappe.db.exists("GP Cue Deck", {"demo_key": data["demo_key"]})
	if existing:
		deck = frappe.get_doc("GP Cue Deck", existing)
	else:
		deck = frappe.new_doc("GP Cue Deck")
	deck.update(
		{
			"title": data["title"],
			"mode": data.get("mode") or "Act",
			"is_demo": 1,
			"demo_key": data["demo_key"],
			"prompts": [{"prompt_text": text} for text in data["prompts"]],
		}
	)
	deck.save(ignore_permissions=True)
	frappe.db.commit()
	return deck


def verify_all() -> list[dict]:
	"""Confirm every shipped demo exists with its expected prompt count."""
	results = []
	for path in demo_files():
		data = json.loads(path.read_text())
		name = frappe.db.exists("GP Cue Deck", {"demo_key": data["demo_key"]})
		ok = bool(name)
		count = 0
		if ok:
			count = frappe.db.count("GP Cue Prompt", {"parent": name, "parenttype": "GP Cue Deck"})
			ok = count >= len(data["prompts"])
		results.append({"demo_key": data["demo_key"], "ok": ok, "prompts": count})
	return results


def hide_all() -> None:
	"""Demos stay playable but disappear from the catalog when a site opts out."""
	for name in frappe.get_all("GP Cue Deck", filters={"is_demo": 1}, pluck="name"):
		frappe.db.set_value("GP Cue Deck", name, "is_demo", 0)
