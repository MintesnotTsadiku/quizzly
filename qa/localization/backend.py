"""Site-integrated localization checks; preserve packs and clean up only our sessions."""

import os
from unittest.mock import patch

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost", sites_path="/home/minte/projects/training-apps/sites")
frappe.connect()
frappe.set_user("Administrator")
from quizzly.demo.amharic import seed_amharic_starters
from quizzly.games import engine
from quizzly.games.api import (
	advance_room,
	create_session,
	get_host_state,
	get_public_state,
	list_public_decks,
	start_session,
)
from quizzly.localization import content_language

session = None
try:
	before = {
		(dt, row.name): row.modified
		for dt in ["QZ Quiz", "GP Crowd Pack", "GP Cue Deck", "GP Draw Pack", "GP Game Pack"]
		for row in frappe.get_all(dt, fields=["name", "modified"])
	}
	packs = seed_amharic_starters()
	after = {
		(dt, row.name): row.modified
		for dt in ["QZ Quiz", "GP Crowd Pack", "GP Cue Deck", "GP Draw Pack", "GP Game Pack"]
		for row in frappe.get_all(dt, fields=["name", "modified"])
	}
	assert before == after, "Repeat seed must not rewrite existing packs"
	assert len(packs) == 25
	for row in packs:
		am = list_public_decks(row["game"], "am")
		en = list_public_decks(row["game"], "en")
		assert any(p["name"] == row["pack"] for p in am), row["game"]
		assert any(p["content_language"] == "am" for p in am)
		assert en and any(p["content_language"] == "en" for p in en), row["game"]
		assert am[0]["content_language"] == "am"
		assert en[0]["content_language"] == "en"
	print("PASS: 25 Amharic packs; English packs remain available; repeat seed changes nothing")
	with patch("frappe.get_cached_doc", return_value=frappe._dict(default_language="am")):
		assert content_language() == "am"
		assert content_language("en") == "en"
	try:
		content_language("invalid")
		raise AssertionError("Invalid language accepted")
	except frappe.ValidationError:
		pass
	print("PASS: site default, explicit override and language validation")
	with patch("frappe.enqueue"):
		created = create_session("common-ground", {"pack": "everyday", "language": "am"})
		session = created["session"]
		start_session(session)
	state = get_host_state(session)
	assert state["configuration"]["language"] == "am"
	assert any("\u1200" <= c <= "\u137f" for c in state["view"]["prompt"])
	assert state["view"]["prompt"] == get_public_state(created["game_pin"])["view"]["prompt"]
	first = state["view"]["prompt"]
	assert get_host_state(session)["view"]["prompt"] == first
	for _ in range(6):
		advance_room(session, get_host_state(session)["state_version"])
	assert get_host_state(session)["status"] == "Ended"
	print("PASS: Amharic host-only game snapshots prompts, reaches shared screen and finishes")
finally:
	if session:
		engine.clear_state(session)
		frappe.cache.srem(engine.ACTIVE_SESSIONS_KEY, session)
		frappe.delete_doc("GP Session", session, ignore_permissions=True, force=True)
		frappe.db.commit()
	frappe.destroy()
