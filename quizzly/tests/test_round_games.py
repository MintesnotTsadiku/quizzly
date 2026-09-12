import time
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from quizzly.demo.seed import ROUND_DEMO_TITLES
from quizzly.games import engine as gpe
from quizzly.games import manifests
from quizzly.games.api import (
	ROUND_GAME_KEYS,
	create_session,
	get_host_state,
	get_player_state,
	get_public_state,
	join_session,
	start_session,
	submit_action,
)
from quizzly.games.round_games.game import PROFILES


class TestRoundGameCatalog(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def cleanup_session(self, session):
		gpe.clear_state(session)
		frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, session)
		for dt in (
			"GP Score Event",
			"GP Action",
			"GP Round",
			"GP Team Membership",
			"GP Participant",
			"GP Team",
		):
			for name in frappe.get_all(dt, filters={"session": session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Session", session, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_every_planned_game_is_registered_and_has_three_english_demos(self):
		available = {m.key for m in manifests() if m.status in ("Available", "Beta")}
		self.assertTrue(set(ROUND_DEMO_TITLES).issubset(available))
		for key in ROUND_DEMO_TITLES:
			self.assertGreaterEqual(
				frappe.db.count("GP Game Pack", {"game_key": key, "is_demo": 1, "content_language": "en"}),
				3,
				key,
			)

	def test_every_round_profile_has_content_preview_metadata(self):
		self.assertEqual(ROUND_GAME_KEYS, set(PROFILES))

	def test_numeric_round_is_secret_scored_and_reconnectable(self):
		pack = frappe.db.get_value("GP Game Pack", {"game_key": "closest-call", "is_demo": 1})
		created = create_session("closest-call", {"pack": pack, "seconds": 15, "rounds": 1})
		session, pin = created["session"], created["game_pin"]
		players = {n: join_session(pin, n) for n in ("Marta", "Samuel", "Yonas")}
		start_session(session)
		frappe.db.commit()
		try:
			public = get_public_state(pin)
			self.assertEqual(public["phase"], "round_open")
			self.assertNotIn("target", public["view"])
			self.assertNotIn("answer", public["view"])
			for n, value in zip(players, (9, 12, 40), strict=True):
				submit_action(
					pin, players[n]["participant_token"], "submit", str(uuid.uuid4()), {"value": value}
				)
			state = gpe.get_state(session)
			state["next_ts"] = time.time() - 1
			state["deadline_ts"] = state["next_ts"]
			gpe.set_state(session, state, ttl=120)
			gpe.tick_once()
			self.assertEqual(get_host_state(session)["phase"], "round_reveal")
			# Closest Call is a duel: only the nearest estimate receives the point.
			self.assertEqual(frappe.db.count("GP Score Event", {"session": session}), 1)
		finally:
			self.cleanup_session(session)

	def test_bluffline_has_anonymous_submission_and_vote_phases(self):
		pack = frappe.db.get_value("GP Game Pack", {"game_key": "bluffline", "is_demo": 1})
		created = create_session("bluffline", {"pack": pack, "seconds": 15, "rounds": 1})
		session, pin = created["session"], created["game_pin"]
		players = {n: join_session(pin, n) for n in ("Liya", "Dawit", "Hana")}
		start_session(session)
		frappe.db.commit()
		try:
			for n, text in zip(
				players, ("A ceremonial basket", "An old measuring stick", "A travel cloak"), strict=True
			):
				submit_action(
					pin, players[n]["participant_token"], "submit", str(uuid.uuid4()), {"value": text}
				)
			state = gpe.get_state(session)
			transition = (
				__import__("quizzly.games", fromlist=["get_game_module"])
				.get_game_module("bluffline")
				.advance_state(
					gpe.context_for(frappe.get_doc("GP Session", session)), state, {"command": "deadline"}
				)
			)
			gpe.apply_transition(frappe.get_doc("GP Session", session), state, transition)
			liya = get_player_state(pin, players["Liya"]["participant_token"])["view"]
			self.assertEqual(liya["phase"], "vote_open")
			self.assertNotIn("A ceremonial basket", [c["value"] for c in liya["choices"]])
			submit_action(
				pin, players["Liya"]["participant_token"], "vote", str(uuid.uuid4()), {"value": "truth"}
			)
		finally:
			self.cleanup_session(session)
