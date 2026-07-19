"""Server-authoritative game loop and hot state for live sessions.

One RQ job per active session drives the whole game. Clients never tick:
each question payload carries a server-set deadline_ts and clients render
their own countdown. Redis (frappe.cache) is the fast gate for submit
validation; the DB is the durable record.
"""

import time

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_seconds

GRACE_SECONDS = 1.0
STATS_SECONDS = 5
GETREADY_SECONDS = 3
# ponytail: host gets 5 minutes to hit Next, then the game moves on by itself
ADVANCE_WAIT_CAP = 300
POLL_SECONDS = 0.25
STATE_TTL_MARGIN = 30
STREAK_CALLOUT_MIN = 3


def enqueue_game_loop(session_doc) -> None:
	total_seconds = sum(question_window(q, session_doc) for q in get_quiz_questions(session_doc))
	question_count = len(get_quiz_questions(session_doc))
	per_question_overhead = (
		GETREADY_SECONDS + STATS_SECONDS + (0 if session_doc.auto_advance else ADVANCE_WAIT_CAP)
	)
	timeout = int(total_seconds + question_count * (per_question_overhead + GRACE_SECONDS) + 60)
	frappe.enqueue(
		"quizzly.engine.run_game_loop",
		queue="long",
		timeout=timeout,
		job_id=f"qz_session_{session_doc.name}",
		deduplicate=True,
		enqueue_after_commit=True,
		session=session_doc.name,
	)


def run_game_loop(session: str) -> None:
	session_doc = frappe.get_doc("QZ Session", session)
	if session_doc.status != "Active":
		return
	questions = get_quiz_questions(session_doc)
	total = len(questions)
	clear_control(session)

	for index, question in enumerate(questions):
		if get_ready(session_doc, question, index, total) == "end":
			break
		deadline_ts = open_question(session_doc, question, index, total)
		control = wait_question_window(session, deadline_ts)
		close_question(session_doc, question, index, total)
		if control == "end" or index == total - 1:
			break
		if wait_before_next(session_doc) == "end":
			break

	finish_session(session_doc)


# Loop steps


def get_ready(session_doc, question, index: int, total: int) -> str | None:
	"""Read-the-question pause before the clock starts, Kahoot style."""
	deadline_ts = time.time() + GETREADY_SECONDS
	set_state(
		session_doc.name,
		{
			"status": "get_ready",
			"q_index": index,
			"question_row": question.name,
			"opened_at": time.time(),
			"deadline_ts": deadline_ts,
			"window_ms": question_window(question, session_doc) * 1000,
			"total": total,
		},
		ttl=GETREADY_SECONDS + STATE_TTL_MARGIN,
	)
	publish_session_event(
		session_doc,
		{
			"type": "get_ready",
			"q_index": index,
			"total": total,
			"question_text": question.question_text,
			"seconds": GETREADY_SECONDS,
		},
	)
	frappe.db.commit()
	while time.time() < deadline_ts:
		if pop_control(session_doc.name, ("end",)):
			return "end"
		time.sleep(POLL_SECONDS)
	return None


def open_question(session_doc, question, index: int, total: int) -> float:
	window = question_window(question, session_doc)
	opened_at = time.time()
	deadline_ts = opened_at + window
	set_state(
		session_doc.name,
		{
			"status": "question",
			"q_index": index,
			"question_row": question.name,
			"opened_at": opened_at,
			"deadline_ts": deadline_ts,
			"window_ms": window * 1000,
			"total": total,
		},
		ttl=window + STATE_TTL_MARGIN,
	)
	frappe.db.set_value("QZ Session", session_doc.name, "current_question", index)
	publish_session_event(session_doc, question_payload(session_doc, question, index, total, deadline_ts))
	frappe.db.commit()
	return deadline_ts


def wait_question_window(session: str, deadline_ts: float) -> str | None:
	"""Sleep until deadline + grace, waking early on host skip/end."""
	while time.time() < deadline_ts + GRACE_SECONDS:
		control = pop_control(session, ("skip", "end"))
		if control:
			return control
		time.sleep(POLL_SECONDS)
	return None


def close_question(session_doc, question, index: int, total: int) -> None:
	state = get_state(session_doc.name) or {}
	window_ms = state.get("window_ms") or question_window(question, session_doc) * 1000
	set_state(
		session_doc.name,
		{**state, "status": "closed"},
		ttl=ADVANCE_WAIT_CAP + STATE_TTL_MARGIN,
	)
	participants = get_live_participants(session_doc.name)
	answers = frappe.get_all(
		"QZ Answer",
		filters={"session": session_doc.name, "question_row": question.name},
		fields=["name", "participant", "selected_option", "response_ms"],
	)
	answer_by_participant = {a.participant: a for a in answers}
	distribution = {"1": 0, "2": 0, "3": 0, "4": 0}

	for participant in participants:
		answer = answer_by_participant.get(participant.name)
		if not answer:
			participant.streak = 0
			frappe.db.set_value("QZ Participant", participant.name, "streak", 0)
			continue
		distribution[str(answer.selected_option)] += 1
		is_correct = str(answer.selected_option) == str(question.correct_option)
		if is_correct:
			participant.streak += 1
			points = compute_points(
				answer.response_ms, window_ms, participant.streak, int(question.points_multiplier or 1)
			)
		else:
			participant.streak = 0
			points = 0
		participant.score += points
		frappe.db.set_value("QZ Answer", answer.name, {"is_correct": int(is_correct), "points": points})
		frappe.db.set_value(
			"QZ Participant",
			participant.name,
			{"score": participant.score, "streak": participant.streak},
		)

	top_5 = [
		{"nickname": p.nickname, "avatar": p.avatar, "score": p.score}
		for p in sorted(participants, key=lambda p: -p.score)[:5]
	]
	streaks = [
		{"nickname": p.nickname, "avatar": p.avatar, "streak": p.streak}
		for p in sorted(participants, key=lambda p: -p.streak)
		if p.streak >= STREAK_CALLOUT_MIN
	][:3]
	publish_session_event(
		session_doc,
		{
			"type": "question_closed",
			"q_index": index,
			"total": total,
			"question_row": question.name,
			"correct_option": question.correct_option,
			"distribution": distribution,
			"top_5": top_5,
			"streaks": streaks,
			"is_last": index == total - 1,
		},
	)
	frappe.cache.delete_value(answered_key(session_doc.name, question.name))
	frappe.db.commit()


def wait_before_next(session_doc) -> str | None:
	"""Stats pause; then auto-advance, or wait (capped) for host next_question."""
	waited = 0.0
	# read fresh: the host can flip auto-advance mid-game
	auto_advance = frappe.db.get_value("QZ Session", session_doc.name, "auto_advance")
	cap = STATS_SECONDS if auto_advance else STATS_SECONDS + ADVANCE_WAIT_CAP
	while waited < cap:
		control = pop_control(session_doc.name, ("advance", "end"))
		if control:
			return control
		time.sleep(POLL_SECONDS)
		waited += POLL_SECONDS
	return None


def is_loop_alive(session: str) -> bool:
	"""Every loop phase re-sets state with a TTL that outlives that phase, so no state = no loop."""
	return get_state(session) is not None


def is_abandoned(session_doc) -> bool:
	"""Active but nothing is driving it: the worker died or was restarted mid-game.

	The age check covers the gap between start_session and the loop's first state write.
	"""
	if session_doc.status != "Active" or is_loop_alive(session_doc.name):
		return False
	last_touched = session_doc.started_at or session_doc.modified
	return time_diff_in_seconds(now_datetime(), last_touched) > STATE_TTL_MARGIN


def end_active_session(session_doc) -> None:
	"""Ask the loop to stop. With no loop left to read the flag, end it here instead."""
	if is_loop_alive(session_doc.name):
		set_control(session_doc.name, "end")
	else:
		finish_session(session_doc)


def finish_session(session_doc) -> None:
	participants = get_live_participants(session_doc.name)
	participants.sort(key=lambda p: (-p.score, p.joined_at or now_datetime()))
	leaderboard = []
	for rank, participant in enumerate(participants, start=1):
		frappe.db.set_value("QZ Participant", participant.name, "rank", rank)
		leaderboard.append(
			{
				"nickname": participant.nickname,
				"avatar": participant.avatar,
				"score": participant.score,
				"rank": rank,
			}
		)
	frappe.db.set_value(
		"QZ Session",
		session_doc.name,
		{"status": "Ended", "ended_at": now_datetime()},
	)
	publish_session_event(
		session_doc,
		{"type": "podium", "top_3": leaderboard[:3], "leaderboard": leaderboard},
	)
	clear_state(session_doc.name)
	frappe.db.commit()


# Scoring


def compute_points(response_ms: int, window_ms: int, streak: int, multiplier: int) -> int:
	"""Kahoot formula. `streak` is the participant's streak including this answer."""
	response_ms = min(max(response_ms or 0, 0), window_ms)
	base = round((1 - (response_ms / window_ms) / 2) * 1000)
	bonus = min(streak - 1, 5) * 50
	return (base + bonus) * multiplier


# Redis state


def state_key(session: str) -> str:
	return f"qz:{session}:state"


def answered_key(session: str, question_row: str) -> str:
	return f"qz:{session}:answered:{question_row}"


def control_key(session: str) -> str:
	return f"qz:{session}:control"


def set_state(session: str, state: dict, ttl: float) -> None:
	frappe.cache.set_value(state_key(session), state, expires_in_sec=int(ttl))


def get_state(session: str) -> dict | None:
	return frappe.cache.get_value(state_key(session))


def clear_state(session: str) -> None:
	frappe.cache.delete_value(state_key(session))
	frappe.cache.delete_value(control_key(session))


def set_control(session: str, command: str) -> None:
	frappe.cache.set_value(control_key(session), command, expires_in_sec=ADVANCE_WAIT_CAP)


def pop_control(session: str, accepted: tuple) -> str | None:
	control = frappe.cache.get_value(control_key(session), use_local_cache=False)
	if control in accepted:
		frappe.cache.delete_value(control_key(session))
		return control
	return None


def clear_control(session: str) -> None:
	frappe.cache.delete_value(control_key(session))


def mark_answered(session: str, question_row: str, participant: str, ttl: float) -> bool:
	"""Fast duplicate pre-check. Returns False if this participant already answered."""
	if has_answered(session, question_row, participant):
		return False
	key = answered_key(session, question_row)
	frappe.cache.sadd(key, participant)
	frappe.cache.expire(frappe.cache.make_key(key), int(ttl))
	return True


def has_answered(session: str, question_row: str, participant: str) -> bool:
	return bool(frappe.cache.sismember(answered_key(session, question_row), participant))


def answered_count(session: str, question_row: str) -> int:
	return len(frappe.cache.smembers(answered_key(session, question_row)))


# Helpers


def question_payload(session_doc, question, index: int, total: int, deadline_ts: float) -> dict:
	"""Hand-built payload: correct_option must never ride along."""
	return {
		"type": "question",
		"q_index": index,
		"total": total,
		"question_row": question.name,
		"question_text": question.question_text,
		"options": [question.option_1, question.option_2, question.option_3, question.option_4],
		"deadline_ts": deadline_ts,
		# clients count down from this instead of deadline_ts, so client clock skew cannot matter
		"window_ms": question_window(question, session_doc) * 1000,
		"randomize_answer_order": int(session_doc.randomize_answer_order or 0),
		"points_multiplier": int(question.points_multiplier or 1),
	}


def question_window(question, session_doc) -> int:
	return question.time_limit or get_quiz(session_doc).default_time_limit or 20


def get_quiz(session_doc):
	return frappe.get_cached_doc("QZ Quiz", session_doc.quiz)


def get_quiz_questions(session_doc):
	return get_quiz(session_doc).questions


def get_live_participants(session: str) -> list:
	return frappe.get_all(
		"QZ Participant",
		filters={"session": session, "kicked": 0},
		fields=["name", "nickname", "avatar", "score", "streak", "joined_at"],
	)


def publish_session_event(session_doc, message: dict) -> None:
	room = f"qz_session_{session_doc.game_pin}"
	frappe.publish_realtime(event=room, message=message, room=room, after_commit=True)
