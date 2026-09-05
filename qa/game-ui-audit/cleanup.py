"""Clean up only the explicitly inventoried records created by game UI audit QA."""

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
for inventory in ("/tmp/gp-ui-audit-sessions.json", "/tmp/gp-ui-native-sessions.json"):
	if Path(inventory).exists():
		names.update(json.loads(Path(inventory).read_text()))
for name in names:
	if not frappe.db.exists("GP Session", name):
		continue
	doc = frappe.get_doc("GP Session", name)
	assert doc.host == "church-browser-qa@circle.localhost"
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
