import os
from unittest.mock import patch

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost", sites_path="/home/minte/projects/training-apps/sites")
frappe.connect()
frappe.set_user("church-browser-qa@circle.localhost")
from quizzly.games import engine
from quizzly.games.api import (
	advance_room,
	create_session,
	get_host_state,
	get_public_state,
	start_session,
)

name = None
try:
	with patch("frappe.enqueue"):
		created = create_session("common-ground", {"pack": "everyday"})
		name = created["session"]
		start_session(name)
	state = get_host_state(name)
	assert state["phase"] == "room_prompt"
	assert not state["participants"]
	version = state["state_version"]
	advance_room(name, version)
	assert get_host_state(name)["phase"] == "room_share"
	advance_room(name, version)
	assert get_host_state(name)["phase"] == "room_share"
	assert get_public_state(created["game_pin"])["view"] == {
		k: v
		for k, v in get_host_state(name)["view"].items()
		if k not in ("paused", "can_previous", "presentation_replay")
	}
	owner = frappe.session.user
	frappe.set_user("Guest")
	try:
		advance_room(name, version + 1)
		raise AssertionError("Guest accessed host")
	except frappe.PermissionError:
		pass
	finally:
		frappe.set_user(owner)
	for _ in range(5):
		advance_room(name, get_host_state(name)["state_version"])
	assert get_host_state(name)["status"] == "Ended"
	print(
		"PASS: no-controller start, private/public views, retry idempotence, guest denial, all six beats, cooperative finish"
	)
finally:
	if name:
		engine.clear_state(name)
		frappe.cache.srem(engine.ACTIVE_SESSIONS_KEY, name)
		frappe.delete_doc("GP Session", name, ignore_permissions=True, force=True)
		frappe.db.commit()
	frappe.destroy()
