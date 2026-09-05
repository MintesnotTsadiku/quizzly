"""Remove only exact QA session IDs from this task's explicit inventory."""

import json
import os
from pathlib import Path

import frappe

bench = Path(__file__).resolve().parents[4]
os.chdir(bench / "sites")
frappe.init(site="training.localhost", sites_path=str(bench / "sites"))
frappe.connect()
frappe.set_user("church-browser-qa@circle.localhost")
from quizzly.games import engine

# Exploratory sessions are listed explicitly; never select records by date or prefix.
names = {"irenptidnl", "s62vg7r0s7", "svrvlua772"}
for inventory in ["/tmp/gp-redesign-session-ids.json", "/tmp/gp-redesign-live-session.json"]:
	if Path(inventory).exists():
		names.update(json.loads(Path(inventory).read_text()))
removed = []
for name in sorted(names):
	if not frappe.db.exists("GP Session", name):
		continue
	doc = frappe.get_doc("GP Session", name)
	assert doc.host == frappe.session.user, "Refusing to clean another host session"
	engine.clear_state(name)
	frappe.cache.srem(engine.ACTIVE_SESSIONS_KEY, name)
	for doctype in ["GP Action", "GP Score Event", "GP Round", "GP Participant", "GP Team"]:
		for record in frappe.get_all(doctype, filters={"session": name}, pluck="name"):
			frappe.delete_doc(doctype, record, ignore_permissions=True, force=True)
	frappe.delete_doc("GP Session", name, ignore_permissions=True, force=True)
	removed.append(name)
frappe.db.commit()
assert not any(frappe.db.exists("GP Session", name) for name in names)
print(json.dumps({"removed": removed, "remaining_owned_sessions": 0}))
frappe.destroy()
