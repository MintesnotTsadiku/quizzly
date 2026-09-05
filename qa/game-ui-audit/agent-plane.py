"""Inspect and interact with the real guide through Agent Plane."""

import json
import os

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost")
frappe.connect()
frappe.set_user("church-browser-qa@circle.localhost")
from agent_plane.runtime.tools import browser_tools as browser

r = browser.browser_start_session(
	base_url="http://127.0.0.1:8081",
	artifact_root="/tmp/gp-ui-audit-agent-plane",
	timeout_ms=20000,
	options={"viewport": {"width": 1440, "height": 1100}},
)
assert r.get("ok"), r.get("error")
sid = r["session_id"]
frappe.db.commit()
try:
	for action in [
		{"action": "open_url", "url": "/play/games/dots-and-boxes?lang=en", "wait_until": "domcontentloaded"},
		{"action": "wait_for", "selector": ".gp-example"},
		{"action": "screenshot", "name": "dots-and-boxes-guide.png", "full_page": True},
		{"action": "open_url", "url": "/play/games/group-sudoku?lang=en", "wait_until": "domcontentloaded"},
		{"action": "wait_for", "selector": ".gp-example"},
		{"action": "screenshot", "name": "group-sudoku-guide.png", "full_page": True},
		{"action": "get_console_errors"},
		{"action": "get_network_errors"},
	]:
		result = browser.browser_session_action(sid, action)
		print(
			json.dumps(
				{
					"action": action["action"],
					"ok": result.get("ok"),
					"result": result.get("result")
					if action["action"] in ["screenshot", "get_console_errors", "get_network_errors"]
					else None,
				},
				default=str,
			),
			flush=True,
		)
		assert result.get("ok"), result.get("error")
		frappe.db.commit()
finally:
	browser.browser_close_session(sid)
	frappe.db.commit()
	frappe.destroy()
