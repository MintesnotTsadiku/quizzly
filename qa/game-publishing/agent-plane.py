"""Verify the actual localized setup through the installed Agent Plane browser."""

import json
import os
from pathlib import Path

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost")
frappe.connect()
frappe.set_user("Administrator")
from agent_plane.runtime.tools import browser_tools as browser

r = browser.browser_start_session(
	base_url="http://127.0.0.1:8081",
	artifact_root="/tmp/quizzly-publishing-agent-plane",
	timeout_ms=20000,
	options={"viewport": {"width": 390, "height": 844}},
)
assert r.get("ok"), r.get("error")
sid = r["session_id"]
frappe.db.commit()
records = []
try:
	for action in [
		{"action": "open_url", "url": "/play/games/common-ground?lang=am"},
		{"action": "wait_for", "selector": ".batch-picker input"},
		{"action": "fill", "selector": ".batch-picker input", "value": "2"},
		{"action": "screenshot", "name": "amharic-count-selection.png", "full_page": True},
		{"action": "get_console_errors"},
		{"action": "get_network_errors"},
	]:
		result = browser.browser_session_action(sid, action)
		record = {"action": action["action"], "ok": result.get("ok")}
		if action["action"] in ("get_console_errors", "get_network_errors", "screenshot"):
			record["result"] = result.get("result")
		records.append(record)
		print(json.dumps(record, default=str), flush=True)
		assert result.get("ok"), result.get("error")
		frappe.db.commit()
finally:
	browser.browser_close_session(sid)
	frappe.db.commit()
	frappe.destroy()
	Path(
		"/home/minte/projects/training-apps/apps/quizzly/docs/game-publishing/evidence/agent-plane.json"
	).write_text(json.dumps(records, default=str, indent=2))
