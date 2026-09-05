"""Remove only explicitly recorded browser fixtures, never date/prefix matches."""

import json
import os
from pathlib import Path

import frappe

bench = Path(__file__).resolve().parents[4]
os.chdir(bench / "sites")
frappe.init(site="training.localhost", sites_path=str(bench / "sites"))
frappe.connect()
frappe.set_user("Administrator")
from quizzly import engine as qz
from quizzly.games import engine as gp

inventory = json.loads(Path("/tmp/gp-access-inventory.json").read_text())
sessions = {tuple(row) for row in inventory["sessions"] if row[1]}
sessions.add(("GP Session", "g04ctmlgip"))
for file in ["/tmp/gp-access-latest-network.json", "/tmp/gp-redesign-live-session.json"]:
	if Path(file).exists():
		sessions.update(("GP Session", name) for name in json.loads(Path(file).read_text()))
removed = []
for doctype, name in sessions:
	if not frappe.db.exists(doctype, name):
		continue
	doc = frappe.get_doc(doctype, name)
	assert doc.host in ("Guest", "church-browser-qa@circle.localhost")
	if doctype == "GP Session":
		gp.clear_state(name)
		frappe.cache.srem(gp.ACTIVE_SESSIONS_KEY, name)
		children = [
			"GP Action",
			"GP Score Event",
			"GP Round",
			"GP Team Membership",
			"GP Participant",
			"GP Team",
		]
	else:
		qz.clear_state(name)
		frappe.cache.srem(qz.ACTIVE_SESSIONS_KEY, name)
		children = ["QZ Answer", "QZ Participant"]
	for child in children:
		if frappe.get_meta(child).has_field("session"):
			for row in frappe.get_all(child, filters={"session": name}, pluck="name"):
				frappe.delete_doc(child, row, ignore_permissions=True, force=True)
	frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
	removed.append([doctype, name])
for name in set(inventory["packs"]):
	if frappe.db.exists("GP Crowd Pack", name):
		doc = frappe.get_doc("GP Crowd Pack", name)
		assert doc.owner in ("Guest", "church-browser-qa@circle.localhost") and not doc.is_demo
		frappe.delete_doc("GP Crowd Pack", name, ignore_permissions=True, force=True)
		removed.append(["GP Crowd Pack", name])
frappe.db.commit()
print(json.dumps({"removed": removed}))
frappe.destroy()
