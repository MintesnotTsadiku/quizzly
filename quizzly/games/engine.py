"""Server-authoritative orchestrator for GatherPlay sessions.

The GP twin of quizzly.engine: one shared self-looping RQ ticker advances every active
GP session by calling into its registered module. Modules return Transitions; this file
owns the Redis hot state, the round rows, the score-event ledger and every realtime
publish, so a module can never bypass the platform.
"""

import time
import uuid

import frappe
from frappe.utils import now_datetime, time_diff_in_seconds

from quizzly.games import GameContext, Resolution, Transition, get_game_module
from quizzly.games.board_session import BOARD_GAME_KEYS

GRACE_SECONDS = 1.0
ADVANCE_WAIT_CAP = 300
TICK_SECONDS = 0.5
PROGRESS_THROTTLE = 0.3
STATE_TTL_MARGIN = 30
ACTIVE_SESSIONS_KEY = "gp:active_sessions"
TICKER_TIMEOUT = 21600
SCHEMA_VERSION = 1


def context_for(session_doc) -> GameContext:
	# a JSON field can come back as a raw string off a plain db read; modules index into it
	configuration = dict(frappe.parse_json(session_doc.get("configuration")) or {})
	from quizzly.batches import batch_of

	batch = batch_of(session_doc)
	if batch:
		configuration["_selected_ids"] = batch["selected"]
	return GameContext(
		session=session_doc.name,
		pin=session_doc.game_pin,
		game_key=session_doc.game_key,
		configuration=configuration,
	)


def enqueue_game_loop(session_doc, first_transition: Transition) -> None:
	"""Seed the module's first phase, register the session, wake the shared ticker."""
	apply_transition(session_doc, {}, first_transition)
	frappe.cache.sadd(ACTIVE_SESSIONS_KEY, session_doc.name)
	frappe.enqueue(
		"quizzly.games.engine.run_ticker",
		queue="long",
		timeout=TICKER_TIMEOUT,
		job_id="gp_ticker",
		deduplicate=True,
		enqueue_after_commit=True,
	)


def run_ticker() -> None:
	"""One shared self-looping job for every live GatherPlay game."""
	while True:
		if not tick_once():
			break
		time.sleep(TICK_SECONDS)


def tick_once() -> bool:
	"""One pass over every active session. Returns False when none are left."""
	session_cache: dict = {}
	sessions = active_sessions()
	if not sessions:
		return False
	prune_caches(sessions, session_cache)
	for session in sessions:
		frappe.db.savepoint("gp_tick")
		try:
			state = get_state(session)
			if not state:
				frappe.cache.srem(ACTIVE_SESSIONS_KEY, session)
				continue
			control = pop_control(session)
			if control and control["command"] == "pause":
				pause_session(session, state)
				frappe.db.commit()
				continue
			if control and control["command"] == "resume":
				resume_session(session, state)
				frappe.db.commit()
				continue
			if state.get("paused"):
				# A paused room deliberately ignores all progression commands except
				# resume/end. Inputs are rejected at the API gate while it is paused.
				frappe.db.commit()
				continue
			if control and control["command"] == "end":
				finish_session(frappe.get_doc("GP Session", session))
				frappe.db.commit()
				continue
			if control and control["command"] == "previous":
				show_previous(session, state)
				frappe.db.commit()
				continue
			if state.get("presentation_replay") and control and control["command"] == "next":
				restore_replay(session, state)
				frappe.db.commit()
				continue
			due = time.time() >= state["next_ts"]
			module = None
			if due and not control:
				doc_for_policy = frappe.get_doc("GP Session", session)
				module = get_game_module(doc_for_policy.game_key)
				if not (frappe.parse_json(doc_for_policy.configuration) or {}).get(
					"auto_progress", True
				) and module.is_presentation_phase(state["phase"]):
					# Hold settled results indefinitely in manual mode. The host's Next
					# command still takes the normal module transition.
					state["next_ts"] = time.time() + ADVANCE_WAIT_CAP
					state["deadline_ts"] = state["next_ts"]
					set_state(session, state, ttl=ADVANCE_WAIT_CAP + STATE_TTL_MARGIN)
					frappe.db.commit()
					continue
			if control or due:
				try:
					doc = frappe.get_doc("GP Session", session)
				except frappe.DoesNotExistError:
					# the row went away under a live game (test cleanup, admin delete)
					frappe.cache.srem(ACTIVE_SESSIONS_KEY, session)
					clear_state(session)
					continue
				module = module or get_game_module(doc.game_key)
				trigger = control or {"command": "deadline"}
				transition = module.advance_state(context_for(doc), state, trigger)
				if transition:
					apply_transition(doc, state, transition)
			else:
				maybe_push_progress(session, state, session_cache)
			frappe.db.commit()
		except Exception:
			# one bad game must not stall every other live room
			frappe.db.rollback(save_point="gp_tick")
			frappe.log_error(title=f"gp_ticker session {session}")
	return True


def maybe_push_progress(session: str, state: dict, session_cache: dict) -> None:
	"""Broadcast the module's live counter on change, at most every PROGRESS_THROTTLE."""
	doc = cached_session_doc(session, session_cache)
	metric = get_game_module(doc.game_key).progress_metric(context_for(doc), state)
	if not metric:
		return
	key = metric_key(metric)
	prev = session_cache.setdefault(session, {}).setdefault("progress")
	now = time.time()
	if prev and prev[0] == key:
		if prev[1] == metric["count"] or now - prev[2] < PROGRESS_THROTTLE:
			return
	elif metric["count"] == 0:
		session_cache[session]["progress"] = (key, 0, now)
		return
	session_cache[session]["progress"] = (key, metric["count"], now)
	publish_session_event(doc, state, "platform.action_progress", metric)


def cached_session_doc(session: str, session_cache: dict):
	"""Pin and configuration never change mid-game, so the ticker reads them once."""
	cached = session_cache.get(session, {}).get("doc")
	if cached:
		return cached
	pin, game_key, configuration = frappe.db.get_value(
		"GP Session", session, ["game_pin", "game_key", "configuration"]
	)
	doc = frappe._dict(
		name=session,
		game_pin=pin,
		game_key=game_key,
		configuration=frappe.parse_json(configuration) or {},
	)
	session_cache.setdefault(session, {})["doc"] = doc
	return doc


def metric_key(metric: dict) -> tuple:
	return tuple(sorted((k, v) for k, v in metric.items() if k != "count"))


def prune_caches(sessions: list[str], *caches: dict) -> None:
	live = set(sessions)
	for cache in caches:
		for stale in [s for s in cache if s not in live]:
			del cache[stale]


def apply_transition(session_doc, old_state: dict, transition: Transition) -> None:
	"""Persist one step: version bump, round bookkeeping, ledger writes, publish."""
	if transition.finished:
		finish_session(session_doc, transition.finished)
		return

	version = (old_state.get("version") or 0) + 1
	now = time.time()
	next_ts = transition.next_ts if transition.next_ts is not None else now + ADVANCE_WAIT_CAP
	ttl = transition.ttl if transition.ttl is not None else (next_ts - now) + STATE_TTL_MARGIN

	if transition.resolution:
		settle_round(session_doc.name, old_state, transition.resolution)

	module_state = dict(transition.module_state)
	new_state = {
		**old_state,
		"schema_version": SCHEMA_VERSION,
		"game_key": session_doc.game_key,
		"session_status": "Active",
		"phase": transition.phase,
		"version": version,
		"deadline_ts": next_ts,
		"next_ts": next_ts,
		"module_state": module_state,
	}
	if old_state and get_game_module(session_doc.game_key).is_presentation_phase(old_state.get("phase", "")):
		history = list(old_state.get("presentation_history") or [])
		# Keep only settled snapshots; no live state, tokens, answers, or secrets.
		history.append(
			{
				k: v
				for k, v in old_state.items()
				if k not in {"presentation_history", "presentation_replay", "return_state"}
			}
		)
		new_state["presentation_history"] = history[-8:]
	elif old_state.get("presentation_history"):
		new_state["presentation_history"] = old_state["presentation_history"]
	from quizzly.batches import observe_transition

	observe_transition(session_doc, new_state)
	set_state(session_doc.name, new_state, ttl=ttl)

	round_index = module_state.get("round_index")
	if round_index is not None:
		if round_index != session_doc.get("current_round"):
			frappe.db.set_value("GP Session", session_doc.name, "current_round", round_index)
		open_round_row(session_doc.name, module_state, next_ts)

	if session_doc.game_key in BOARD_GAME_KEYS and module_state.get("rules_version") == 2:
		from quizzly.games.board_session import checkpoint

		checkpoint(session_doc, new_state)

	payload = {"phase": transition.phase, **(transition.publish or {})}
	if session_doc.game_key in BOARD_GAME_KEYS and module_state.get("rules_version") == 2:
		payload.update(revision=version, paused=bool(new_state.get("paused")))
	publish_session_event(
		session_doc,
		new_state,
		payload.get("type") or "platform.state_changed",
		payload,
		deadline_ts=next_ts,
	)


def open_round_row(session: str, module_state: dict, deadline_ts: float) -> str | None:
	"""One durable row per round, opened by the state write that starts it."""
	index = module_state.get("round_index")
	if index is None:
		return None
	existing = get_round_name(session, index)
	if existing:
		return existing
	round_doc = frappe.get_doc(
		{
			"doctype": "GP Round",
			"session": session,
			"round_index": index,
			"module_key": module_state.get("round_key"),
			"status": "Open",
			"actor_team": module_state.get("actor_team"),
			"actor_participant": module_state.get("actor_participant"),
			"opened_at": now_datetime(),
			"deadline_ts": now_datetime(),
		}
	).insert(ignore_permissions=True)
	return round_doc.name


def settle_round(session: str, old_state: dict, resolution: Resolution) -> None:
	import json

	module_state = old_state.get("module_state") or {}
	round_name = get_round_name(session, module_state.get("round_index"))
	if round_name:
		frappe.db.set_value(
			"GP Round",
			round_name,
			{
				"status": "Resolved",
				"resolved_at": now_datetime(),
				# db.set_value does not encode dicts; the column takes a JSON string
				"resolution": json.dumps(resolution.summary),
			},
			modified=now_datetime(),
		)
	apply_deltas(session, resolution.deltas, round_index=module_state.get("round_index") or 0)


def apply_deltas(session: str, deltas: list, round_index: int = 0) -> None:
	"""Write immutable ledger rows, then materialize totals on teams and participants."""
	for delta in deltas:
		if frappe.db.exists("GP Score Event", {"session": session, "idempotency_key": delta.idempotency_key}):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "GP Score Event",
					"session": session,
					"round_index": round_index,
					"subject_type": delta.subject_type,
					"subject": delta.subject,
					"points": delta.points,
					"category": delta.category,
					"raw_metric": delta.raw_metric,
					"idempotency_key": delta.idempotency_key,
				}
			).insert(ignore_permissions=True)
		except frappe.UniqueValidationError:
			# A worker ticker and a deterministic test/browser tick may settle the
			# same transition concurrently. The DB key is the final idempotency gate.
			continue
		doctype = "GP Team" if delta.subject_type == "Team" else "GP Participant"
		frappe.db.sql(
			f"update `tab{doctype}` set score = coalesce(score, 0) + %(points)s where name = %(name)s",
			{"points": delta.points, "name": delta.subject},
		)


def finish_session(session_doc, result=None) -> None:
	status = frappe.db.get_value("GP Session", session_doc.name, "status", for_update=True)
	if status in ("Ended", "Cancelled"):
		return
	state = get_state(session_doc.name) or {"module_state": {}, "version": 0}
	result = result or get_game_module(session_doc.game_key).finish_game(context_for(session_doc), state)
	persist_leaderboard(result.leaderboard)
	frappe.db.set_value("GP Session", session_doc.name, {"status": "Ended", "ended_at": now_datetime()})
	publish_session_event(session_doc, state, "platform.session_ended", result.publish)
	clear_state(session_doc.name)
	frappe.cache.srem(ACTIVE_SESSIONS_KEY, session_doc.name)
	frappe.db.commit()


def persist_leaderboard(leaderboard: list[dict]) -> None:
	for rank, entry in enumerate(leaderboard, start=1):
		doctype = "GP Team" if entry.get("subject_type", "Team") == "Team" else "GP Participant"
		# score rides along: computed standings (e.g. team averages) must land in the
		# record too, or the Ended snapshot reads zeros
		frappe.db.set_value(
			doctype, entry["name"], {"rank": entry.get("rank", rank), "score": entry.get("score", 0)}
		)


# --- hot state ---------------------------------------------------------------


def state_key(session: str) -> str:
	return f"gp:{session}:state"


def control_key(session: str) -> str:
	return f"gp:{session}:control"


def acted_key(session: str, idempotency_key: str) -> str:
	return f"gp:{session}:acted:{idempotency_key}"


def set_state(session: str, state: dict, ttl: float) -> None:
	frappe.cache.set_value(state_key(session), state, expires_in_sec=int(ttl))


def get_state(session: str) -> dict | None:
	# never from process-local cache: the long-lived ticker must see what other
	# processes wrote, or it spins on a vanished session
	state = frappe.cache.get_value(state_key(session), use_local_cache=False)
	if state is None or (
		(state.get("module_state") or {}).get("rules_version") == 2
		and state.get("game_key") in BOARD_GAME_KEYS
	):
		from quizzly.games.board_session import restore

		return restore(session)
	return state


def clear_state(session: str) -> None:
	frappe.cache.delete_value(state_key(session))
	frappe.cache.delete_value(control_key(session))


def pause_session(session: str, state: dict) -> None:
	if state.get("paused"):
		return
	now = time.time()
	state = dict(state)
	state.update({"paused": True, "paused_remaining": max(0.0, state["next_ts"] - now), "paused_at": now})
	set_state(session, state, ttl=ADVANCE_WAIT_CAP + STATE_TTL_MARGIN)
	publish_control_state(session, state)


def resume_session(session: str, state: dict) -> None:
	if not state.get("paused"):
		return
	state = dict(state)
	deadline = time.time() + max(0.0, state.get("paused_remaining", 0.0))
	state.update({"paused": False, "next_ts": deadline, "deadline_ts": deadline})
	state.pop("paused_remaining", None)
	state.pop("paused_at", None)
	set_state(session, state, ttl=max(60, deadline - time.time() + STATE_TTL_MARGIN))
	publish_control_state(session, state)


def show_previous(session: str, state: dict) -> None:
	"""Replay a settled snapshot without mutating its original game state."""
	history = list(state.get("presentation_history") or [])
	if not history:
		return
	snapshot = history.pop()
	replay = dict(snapshot)
	replay.update(
		{
			"presentation_replay": True,
			"return_state": {
				k: v
				for k, v in state.items()
				if k not in {"presentation_history", "presentation_replay", "return_state"}
			},
			"presentation_history": history,
			"next_ts": time.time() + ADVANCE_WAIT_CAP,
			"deadline_ts": time.time() + ADVANCE_WAIT_CAP,
		}
	)
	set_state(session, replay, ttl=ADVANCE_WAIT_CAP + STATE_TTL_MARGIN)
	publish_control_state(session, replay)


def restore_replay(session: str, state: dict) -> None:
	returned = dict(state.get("return_state") or {})
	if not returned:
		return
	returned["presentation_history"] = state.get("presentation_history") or []
	set_state(session, returned, ttl=max(60, returned["next_ts"] - time.time() + STATE_TTL_MARGIN))
	publish_control_state(session, returned)


def publish_control_state(session: str, state: dict) -> None:
	"""Wake every surface after a host-only presentation control.

	Surfaces then fetch their role-scoped snapshot, so this event never turns a
	private prompt or a player answer into a public payload.
	"""
	doc = frappe.get_doc("GP Session", session)
	publish_session_event(doc, state, "platform.state_changed", {"phase": state["phase"]})


def set_control(session: str, control: dict) -> None:
	frappe.cache.set_value(control_key(session), control, expires_in_sec=ADVANCE_WAIT_CAP)


def pop_control(session: str) -> dict | None:
	control = frappe.cache.get_value(control_key(session), use_local_cache=False)
	if isinstance(control, dict) and control.get("command"):
		frappe.cache.delete_value(control_key(session))
		return control
	return None


def mark_acted(session: str, idempotency_key: str, ttl: float) -> bool:
	"""Fast replay pre-check keyed by the client's idempotency key."""
	key = acted_key(session, idempotency_key)
	inserted = frappe.cache.execute_command("SADD", frappe.cache.make_key(key), idempotency_key)
	if not inserted:
		return False
	frappe.cache.expire(frappe.cache.make_key(key), int(ttl))
	return True


def active_sessions() -> list[str]:
	members = frappe.cache.smembers(ACTIVE_SESSIONS_KEY)
	return [m.decode() if isinstance(m, bytes) else m for m in members]


def is_loop_alive(session: str) -> bool:
	return get_state(session) is not None


def is_abandoned(session_doc) -> bool:
	"""Active but nothing is driving it: the worker died or was restarted mid-game."""
	if session_doc.status != "Active" or is_loop_alive(session_doc.name):
		return False
	last_touched = session_doc.started_at or session_doc.modified
	return time_diff_in_seconds(now_datetime(), last_touched) > STATE_TTL_MARGIN


def end_active_session(session_doc, result=None) -> None:
	"""Ask the ticker to stop. With no ticker left to read the flag, end it here."""
	if is_loop_alive(session_doc.name):
		set_control(session_doc.name, {"command": "end"})
	else:
		finish_session(session_doc, result)


# --- rounds, actions, teams --------------------------------------------------


def get_round_name(session: str, round_index: int | None) -> str | None:
	if round_index is None:
		return None
	return frappe.db.get_value("GP Round", {"session": session, "round_index": round_index})


def record_action(
	session_doc, round_name: str | None, participant, action_type: str, payload: dict, idempotency_key: str
) -> str:
	action = frappe.get_doc(
		{
			"doctype": "GP Action",
			"session": session_doc.name,
			"round": round_name,
			"participant": participant.name,
			"team": participant.team,
			"action_type": action_type,
			"payload": payload,
			"received_at": now_datetime(),
			"idempotency_key": idempotency_key,
		}
	)
	action.insert(ignore_permissions=True, ignore_links=True)
	return action.name


def accepted_actions(session: str, round_index: int | None) -> list[frappe._dict]:
	round_name = get_round_name(session, round_index)
	if not round_name:
		return []
	actions = frappe.get_all(
		"GP Action",
		filters={"session": session, "round": round_name, "accepted": 1},
		fields=["name", "participant", "team", "action_type", "payload", "received_at"],
		order_by="creation asc",
	)
	for action in actions:
		if isinstance(action.payload, str):
			action.payload = frappe.parse_json(action.payload)
	return actions


def create_teams(session: str, participants: list[dict], team_count: int) -> list[dict]:
	"""Round-robin the lobby into balanced teams. Returns the team roster."""
	team_count = max(1, min(team_count, len(participants)))
	for membership in frappe.get_all("GP Team Membership", filters={"session": session}, pluck="name"):
		frappe.delete_doc("GP Team Membership", membership, force=True)
	frappe.db.sql(
		"""update `tabGP Participant` set team = null where session = %(session)s""", {"session": session}
	)
	for name in frappe.get_all("GP Team", filters={"session": session}, pluck="name"):
		frappe.delete_doc("GP Team", name, force=True)
	teams = []
	for position in range(team_count):
		team = frappe.get_doc(
			{
				"doctype": "GP Team",
				"session": session,
				"team_name": f"Team {position + 1}",
				"color": TEAM_COLORS[position % len(TEAM_COLORS)],
				"seed": position + 1,
			}
		).insert(ignore_permissions=True)
		teams.append({"name": team.name, "team_name": team.team_name, "color": team.color})
	for position, participant in enumerate(participants):
		team = teams[position % team_count]
		frappe.db.set_value("GP Participant", participant["name"], "team", team["name"])
		frappe.get_doc(
			{
				"doctype": "GP Team Membership",
				"session": session,
				"team": team["name"],
				"participant": participant["name"],
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
	return teams


TEAM_COLORS = ["ember", "lagoon", "gold", "orchid"]


def publish_session_event(
	session_doc, state: dict, event_type: str, payload: dict, deadline_ts: float | None = None
) -> None:
	"""Envelope per architecture §9; events notify, snapshot APIs are authoritative."""
	room = f"gp_session_{session_doc.game_pin}"
	version = (state or {}).get("version") or 0
	envelope = {
		"contract": 1,
		"event_id": uuid.uuid4().hex,
		"seq": version,
		"type": event_type,
		"game": session_doc.game_key,
		"state_version": version,
		"server_ts": time.time(),
		"payload": payload,
	}
	if deadline_ts is not None:
		envelope["deadline_ts"] = deadline_ts
	frappe.publish_realtime(event=room, message=envelope, room=room, after_commit=True)
