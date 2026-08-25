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
}


def demo_files(game_key: str | None = None) -> list[Path]:
	pattern = f"{game_key}/*.json" if game_key else "*/*.json"
	return sorted(DEMO_DIR.glob(pattern))


def seed_all() -> list[dict]:
	return [seed_file(path) for path in demo_files()]


def seed_file(path: Path) -> dict:
	data = json.loads(path.read_text())
	pack = upsert(data)
	return {"demo_key": data["demo_key"], "pack": pack.name, "prompts": len(pack.prompts or [])}


def upsert(data: dict):
	game_key = data["game_key"]
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
	pack.save(ignore_permissions=True)
	frappe.db.commit()
	return pack


def verify_all() -> list[dict]:
	"""Confirm every shipped demo exists with its expected prompt count."""
	results = []
	for path in demo_files():
		data = json.loads(path.read_text())
		pack_doctype = CONTENT[data["game_key"]][0]
		name = frappe.db.exists(pack_doctype, {"demo_key": data["demo_key"]})
		ok = bool(name)
		count = 0
		if ok:
			count = frappe.db.count(
				CONTENT[data["game_key"]][1], {"parent": name, "parenttype": pack_doctype}
			)
			ok = count >= len(data["prompts"])
		results.append({"demo_key": data["demo_key"], "ok": ok, "prompts": count})
	return results


def hide_all() -> None:
	"""Demos stay playable but disappear from the catalog when a site opts out."""
	for pack_doctype, _ in {v[0]: v for v in CONTENT.values()}.values():
		for name in frappe.get_all(pack_doctype, filters={"is_demo": 1}, pluck="name"):
			frappe.db.set_value(pack_doctype, name, "is_demo", 0)
