"""Read catalog content coverage; never emit credentials or private packs."""

import json
import os
from pathlib import Path

import frappe

out = Path("/home/minte/projects/training-apps/apps/quizzly/docs/game-ui-audit/evidence/content.json")
os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost")
frappe.connect()
rows = []
for pack in frappe.get_all(
	"GP Game Pack", filters={"is_demo": 1}, fields=["name", "title", "game_key", "content_language"]
):
	items = frappe.get_all("GP Game Item", filters={"parent": pack.name}, fields=["media_url"])
	rows.append(
		{
			"game": pack.game_key,
			"title": pack.title,
			"language": pack.content_language,
			"items": len(items),
			"with_media": sum(bool(i.media_url) for i in items),
		}
	)
from quizzly.games.round_games.game import RoundGame

out.write_text(
	json.dumps(
		{
			"demo_packs": rows,
			"symbol_normalization_probe": {
				"first": RoundGame().norm("■■■··"),
				"different": RoundGame().norm("■·■■·"),
			},
			"unicode_normalization_probe": {
				"first": RoundGame().norm("ሙዚቃ"),
				"different": RoundGame().norm("ተክሎች"),
			},
		},
		ensure_ascii=False,
		indent=2,
	)
)
print("Read demo coverage:", len(rows), "packs")
frappe.destroy()
