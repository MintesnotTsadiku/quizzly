"""Clean up only the explicitly inventoried records created by Grid Conquest QA."""

import json
import os
from pathlib import Path

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost", sites_path="/home/minte/projects/training-apps/sites")
frappe.connect()
frappe.set_user("Administrator")
from quizzly.games import engine

removed = []
names = set()
for inventory in ("/tmp/gp-grid-before-sessions.json", "/tmp/gp-grid-after-sessions.json"):
	if Path(inventory).exists():
		names.update(json.loads(Path(inventory).read_text()))
# This replay room was captured in failure.png before the test could inventory it.
failed_replay = frappe.db.get_value(
	"GP Session",
	{
		"game_pin": "093534",
		"host": "church-browser-qa@circle.localhost",
		"game_key": "grid-conquest",
		"creation": ["between", ["2026-09-05 22:34:00", "2026-09-05 22:36:00"]],
	},
	"name",
)
if failed_replay:
	names.add(failed_replay)
for name in names:
	if not frappe.db.exists("GP Session", name):
		continue
	doc = frappe.get_doc("GP Session", name)
	assert doc.host == "church-browser-qa@circle.localhost" and doc.game_key == "grid-conquest"
	engine.clear_state(name)
	frappe.cache.srem(engine.ACTIVE_SESSIONS_KEY, name)
	for dt in ["GP Action", "GP Score Event", "GP Round", "GP Team Membership", "GP Participant", "GP Team"]:
		for child in frappe.get_all(dt, filters={"session": name}, pluck="name"):
			frappe.delete_doc(dt, child, ignore_permissions=True, force=True)
	frappe.delete_doc("GP Session", name, ignore_permissions=True, force=True)
	removed.append(name)
frappe.db.commit()
print("Removed only inventoried QA records:", len(removed))
frappe.destroy()
