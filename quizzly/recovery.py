"""Recover stopped game jobs; never reconstruct a round from incomplete data.

RQ owns worker-death detection. A STARTED job is left alone until RQ marks it
failed, avoiding competing tickers. Expired room state ends with saved scores.
"""

import frappe
from frappe.utils.background_jobs import is_job_enqueued

from quizzly.games import get_game_module


def recover_game_loops():
	from quizzly import engine as quiz
	from quizzly.games import engine as games

	for engine, doctype, job_id in ((games, "GP Session", "gp_ticker"), (quiz, "QZ Session", "qz_ticker")):
		# Site-scoped lock prevents overlapping scheduler invocations.
		with frappe.cache.lock(f"quizzly:recovery:{job_id}", timeout=120):
			_recover(engine, doctype, job_id)


def _recover(engine, doctype, job_id):
	live = False
	# Query the DB so a lost Redis active-session index does not hide live rooms.
	for name in frappe.get_all(doctype, filters={"status": "Active"}, pluck="name"):
		frappe.db.savepoint("game_recovery")
		try:
			doc = frappe.get_doc(doctype, name)
			if doc.status != "Active":
				continue
			if engine.get_state(name):
				from quizzly.games.board_session import is_board

				if doctype == "GP Session" and is_board(doc):
					continue
				if (
					doctype == "GP Session"
					and "host_only" in get_game_module(doc.game_key).manifest.capabilities
				):
					continue
				frappe.cache.sadd(engine.ACTIVE_SESSIONS_KEY, name)
				live = True
			elif engine.is_abandoned(doc):
				engine.finish_session(doc)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback(save_point="game_recovery")
			frappe.log_error(title=f"Game recovery: {doctype} {name}")
	if live and not is_job_enqueued(job_id):
		frappe.enqueue(
			f"{engine.__name__}.run_ticker",
			queue="long",
			timeout=engine.TICKER_TIMEOUT,
			job_id=job_id,
			deduplicate=True,
			enqueue_after_commit=True,
		)
