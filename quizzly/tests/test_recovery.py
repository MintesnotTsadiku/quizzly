"""Recovery must preserve active rounds and never compete with a known live job."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from quizzly.recovery import _recover


class TestRecovery(unittest.TestCase):
	def setUp(self):
		self.engine = MagicMock()
		self.engine.__name__ = "quizzly.games.engine"
		self.engine.ACTIVE_SESSIONS_KEY = "gp:active_sessions"
		self.engine.TICKER_TIMEOUT = 21600
		self.doc = SimpleNamespace(name="room", status="Active", game_key="crowd-compass")
		self.db, self.cache = MagicMock(), MagicMock()
		patcher = patch(
			"quizzly.recovery.get_game_module",
			return_value=SimpleNamespace(manifest=SimpleNamespace(capabilities=())),
		)
		self.module = patcher.start()
		self.addCleanup(patcher.stop)
		for target, value in [("frappe.db", self.db), ("frappe.cache", self.cache)]:
			patcher = patch(target, value)
			patcher.start()
			self.addCleanup(patcher.stop)
		for target, result in [("frappe.get_all", ["room"]), ("frappe.get_doc", self.doc)]:
			patcher = patch(target, return_value=result)
			patcher.start()
			self.addCleanup(patcher.stop)

	@patch("frappe.enqueue")
	@patch("quizzly.recovery.is_job_enqueued", return_value=False)
	def test_stopped_job_requeued_without_resetting_round(self, busy, enqueue):
		self.engine.get_state.return_value = {"phase": "prediction_open"}
		_recover(self.engine, "GP Session", "gp_ticker")
		self.cache.sadd.assert_called_once_with("gp:active_sessions", "room")
		self.engine.finish_session.assert_not_called()
		enqueue.assert_called_once_with(
			"quizzly.games.engine.run_ticker",
			queue="long",
			timeout=21600,
			job_id="gp_ticker",
			deduplicate=True,
			enqueue_after_commit=True,
		)

	@patch("frappe.enqueue")
	@patch("quizzly.recovery.is_job_enqueued", return_value=True)
	def test_running_or_queued_job_is_not_replaced(self, busy, enqueue):
		_recover(self.engine, "GP Session", "gp_ticker")
		enqueue.assert_not_called()

	@patch("frappe.enqueue")
	def test_expired_state_ends_with_saved_scores(self, enqueue):
		self.engine.get_state.return_value = None
		self.engine.is_abandoned.return_value = True
		_recover(self.engine, "GP Session", "gp_ticker")
		self.engine.finish_session.assert_called_once_with(self.doc)
		enqueue.assert_not_called()

	@patch("frappe.enqueue")
	def test_startup_grace_is_respected(self, enqueue):
		self.engine.get_state.return_value = None
		self.engine.is_abandoned.return_value = False
		_recover(self.engine, "GP Session", "gp_ticker")
		self.engine.finish_session.assert_not_called()
		enqueue.assert_not_called()

	@patch("frappe.enqueue")
	def test_concurrently_ended_room_is_ignored(self, enqueue):
		self.doc.status = "Ended"
		_recover(self.engine, "GP Session", "gp_ticker")
		self.engine.get_state.assert_not_called()
		enqueue.assert_not_called()

	@patch("frappe.enqueue")
	def test_device_free_room_never_gets_a_timer_job(self, enqueue):
		self.module.return_value.manifest.capabilities = ("host_only",)
		_recover(self.engine, "GP Session", "gp_ticker")
		self.cache.sadd.assert_not_called()
		enqueue.assert_not_called()
