"""CueCast smoke: full game through the real APIs while the RQ worker drives the ticker.

Run with: bench --site training.localhost console < apps/quizzly/scripts/cuecast_smoke.py
"""

import time
import uuid

import frappe

frappe.set_user("Administrator")

from quizzly.games import engine as gpe  # noqa: E402
from quizzly.games.api import (  # noqa: E402
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

created = create_session("cuecast", {"deck": deck.name, "seconds": 30, "teams_count": 2, "sudden_death": 1})
pin = created["game_pin"]
players = {n: join_session(pin, n) for n in ["ada", "bob", "cy", "dee"]}
print("joined:", sorted(players))
start_session(created["session"])
frappe.db.commit()


def wait_phase(target, timeout=45):
	deadline = time.time() + timeout
	while time.time() < deadline:
		hs = get_host_state(created["session"])
		if hs.get("phase") == target:
			return hs
		time.sleep(0.6)
	return None


hs = wait_phase("turn_open")
assert hs, f"never reached turn_open: {get_host_state(created['session'])}"
performer_card = hs["view"]["performer"]
print("turn_open performer:", performer_card["nickname"])

perf_nick = performer_card["nickname"]
perf_token = players[perf_nick]["participant_token"]
ps = get_player_state(pin, perf_token)
print("performer private prompt:", repr(ps["view"].get("prompt")))

other = [n for n in players if n != perf_nick][0]
ops = get_player_state(pin, players[other]["participant_token"])
print("guesser sees prompt?", ops["view"].get("prompt"), "| is_performer:", ops["view"]["is_performer"])

try:
	submit_action(pin, players[other]["participant_token"], "correct_prompt", str(uuid.uuid4()))
	print("non-performer action: ACCEPTED (BUG)")
except Exception as e:
	print("non-performer rejected:", getattr(e, "messages", [""])[0])

for i, action_type in enumerate(["correct_prompt", "correct_prompt", "pass_prompt"]):
	r = submit_action(pin, perf_token, action_type, str(uuid.uuid4()))
	print("action", i, "->", r)

pub = get_public_state(pin)
print("public solved count:", pub["view"]["solved"])
print("public leaks prompt?", [k for k in pub["view"] if "prompt" in k.lower()])

hs = wait_phase("turn_review")
print("review played:", hs["view"]["played"], "solved:", hs["view"]["solved_count"])
hs = wait_phase("scoreboard")
print("scoreboard teams:", [(t["team_name"], t["score"]) for t in hs["view"]["teams"]])

# second turn happens for team 2; let the whole game run to the podium
hs = wait_phase("turn_open", timeout=30)
if hs:
	print("second turn performer:", hs["view"]["performer"]["nickname"], "(no actions)")
hs = wait_phase("podium", timeout=240) or {}
print("final teams:", [(t.get("team_name"), t.get("score"), t.get("rank")) for t in hs.get("podium", [])])
doc = frappe.get_doc("GP Session", created["session"])
print("session status:", doc.status)
events = frappe.get_all("GP Score Event", filters={"session": created["session"]}, fields=["points", "category"])
print("ledger:", events)

# cleanup
for dt in ("GP Score Event", "GP Action", "GP Round", "GP Team Membership"):
	for n in frappe.get_all(dt, filters={"session": created["session"]}, pluck="name"):
		frappe.delete_doc(dt, n, force=True, ignore_permissions=True)
for n in frappe.get_all("GP Participant", filters={"session": created["session"]}, pluck="name"):
	frappe.delete_doc("GP Participant", n, force=True, ignore_permissions=True)
for n in frappe.get_all("GP Team", filters={"session": created["session"]}, pluck="name"):
	frappe.delete_doc("GP Team", n, force=True, ignore_permissions=True)
frappe.delete_doc("GP Session", created["session"], force=True, ignore_permissions=True)
frappe.delete_doc("GP Cue Deck", deck.name, force=True, ignore_permissions=True)
frappe.db.commit()
print("cleaned up")
