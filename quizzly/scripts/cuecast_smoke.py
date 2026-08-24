"""CueCast smoke: full game through the real APIs while the RQ worker drives the ticker.

Run with:
	bench --site training.localhost execute quizzly.scripts.cuecast_smoke.run
"""

import time
import uuid

import frappe

from quizzly.games import engine as gpe


def run():
	frappe.set_user("Administrator")
	from quizzly.games.api import (
		create_session,
		get_host_state,
		get_player_state,
		get_public_state,
		join_session,
		start_session,
		submit_action,
	)

	deck = frappe.get_doc(
		{
			"doctype": "GP Cue Deck",
			"title": "Smoke Deck",
			"mode": "Act",
			"prompts": [
				{"prompt_text": t}
				for t in ["milking a cow", "traffic jam", "walking the dog", "parallel parking"]
			],
		}
	).insert()
	frappe.db.commit()

	created = create_session(
		"cuecast", {"deck": deck.name, "seconds": 30, "teams_count": 2, "sudden_death": 1}
	)
	pin = created["game_pin"]
	players = {n: join_session(pin, n) for n in ["ada", "bob", "cy", "dee"]}
	print("joined:", sorted(players))
	start_session(created["session"])
	frappe.db.commit()

	def wait_phase(target, timeout=45):
		"""Drive the ticker ourselves: deterministic in any environment, worker or not."""
		deadline = time.time() + timeout
		while time.time() < deadline:
			gpe.tick_once()
			hs = get_host_state(created["session"])
			if hs.get("phase") == target or (target == "podium" and hs.get("podium")):
				return hs
			time.sleep(0.3)
		return None

	hs = wait_phase("turn_open")
	assert hs, f"never reached turn_open: {get_host_state(created['session'])}"
	performer_card = hs["view"]["performer"]
	print("turn_open performer:", performer_card["nickname"])

	perf_nick = performer_card["nickname"]
	perf_token = players[perf_nick]["participant_token"]
	ps = get_player_state(pin, perf_token)
	print("performer private prompt:", repr(ps["view"].get("prompt")))

	other = next(n for n in players if n != perf_nick)
	ops = get_player_state(pin, players[other]["participant_token"])
	print("guesser sees prompt?", ops["view"].get("prompt"), "| is_performer:", ops["view"]["is_performer"])

	try:
		submit_action(pin, players[other]["participant_token"], "correct_prompt", str(uuid.uuid4()))
		print("non-performer action: ACCEPTED (BUG)")
	except Exception as e:
		print("non-performer rejected:", getattr(e, "messages", [""])[0])

	for i, action_type in enumerate(["correct_prompt", "correct_prompt", "pass_prompt"]):
		result = submit_action(pin, perf_token, action_type, str(uuid.uuid4()))
		# web requests auto-commit; this script must do it so the ticker can see actions
		frappe.db.commit()
		print("action", i, "->", result)

	pub = get_public_state(pin)
	print("public solved count:", pub["view"]["solved"])
	print("public leaks prompt?", [k for k in pub["view"] if "prompt" in k.lower()])

	hs = wait_phase("turn_review")
	assert hs, "never reached turn_review"
	print("review played:", hs["view"]["played"], "solved:", hs["view"]["solved_count"])
	print(
		"[forensics] rounds:",
		frappe.get_all(
			"GP Round",
			filters={"session": created["session"]},
			fields=["round_index", "status", "resolution"],
		),
	)
	print(
		"[forensics] actions:",
		frappe.get_all(
			"GP Action", filters={"session": created["session"]}, fields=["round", "action_type", "accepted"]
		),
	)
	print(
		"[forensics] events:",
		frappe.get_all(
			"GP Score Event", filters={"session": created["session"]}, fields=["points", "category"]
		),
	)
	print(
		"[forensics] teams:",
		frappe.get_all("GP Team", filters={"session": created["session"]}, fields=["team_name", "score"]),
	)
	hs = wait_phase("scoreboard")
	assert hs, "never reached scoreboard"
	print("scoreboard teams:", [(t["team_name"], t["score"]) for t in hs["view"]["teams"]])

	hs = wait_phase("turn_open", timeout=30)
	if hs:
		print("second turn performer:", hs["view"]["performer"]["nickname"], "(no actions)")
	final = wait_phase("podium", timeout=300) or {}
	print(
		"final teams:", [(t.get("team_name"), t.get("score"), t.get("rank")) for t in final.get("podium", [])]
	)
	doc = frappe.get_doc("GP Session", created["session"])
	print("session status:", doc.status)
	events = frappe.get_all(
		"GP Score Event", filters={"session": created["session"]}, fields=["points", "category"]
	)
	print("ledger:", events)

	cleanup(created["session"], deck.name)
	print("cleaned up")


def cleanup(session: str, deck: str) -> None:
	# take the game off the ticker before deleting rows under it
	gpe.clear_state(session)
	frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, session)
	for dt in ("GP Score Event", "GP Action", "GP Round", "GP Team Membership"):
		for name in frappe.get_all(dt, filters={"session": session}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	for dt in ("GP Participant", "GP Team"):
		for name in frappe.get_all(dt, filters={"session": session}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	frappe.delete_doc("GP Session", session, force=True, ignore_permissions=True)
	frappe.delete_doc("GP Cue Deck", deck, force=True, ignore_permissions=True)
	frappe.db.commit()
