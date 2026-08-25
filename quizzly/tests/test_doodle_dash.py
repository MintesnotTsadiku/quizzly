import time
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from quizzly.games import engine as gpe
from quizzly.games.api import (
	create_session,
	get_host_state,
	get_player_state,
	get_public_state,
	join_session,
	start_session,
	submit_action,
)


class TestDoodleDash(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pack = frappe.get_doc(
			{
				"doctype": "GP Draw Pack",
				"title": "Draw Test",
				"prompts": [
					{"prompt_text": "Tree house", "aliases": "treehouse"},
					{"prompt_text": "Rocket", "aliases": "spaceship"},
				],
			}
		).insert()
		created = create_session("doodle-dash", {"pack": self.pack.name, "seconds": 30, "rounds": 1})
		self.session, self.pin = created["session"], created["game_pin"]
		self.players = {name: join_session(self.pin, name) for name in ("Abel", "Beth", "Chala")}
		start_session(self.session)
		frappe.db.commit()
		self.advance()

	def tearDown(self):
		for round_index in range(2):
			frappe.cache.delete_value(f"gp:doodle:{self.session}:{round_index}:canvas")
		gpe.clear_state(self.session)
		frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, self.session)
		for dt in (
			"GP Score Event",
			"GP Action",
			"GP Round",
			"GP Team Membership",
			"GP Participant",
			"GP Team",
		):
			for name in frappe.get_all(dt, filters={"session": self.session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Session", self.session, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Draw Pack", self.pack.name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def advance(self):
		state = gpe.get_state(self.session)
		state["next_ts"] = time.time() - 1
		state["deadline_ts"] = state["next_ts"]
		gpe.set_state(self.session, state, ttl=120)
		gpe.tick_once()

	def token(self, n):
		return self.players[n]["participant_token"]

	def test_prompt_secrecy_canvas_recovery_and_scoring(self):
		host = get_host_state(self.session)
		self.assertEqual(host["phase"], "draw_open")
		artist = host["view"]["artist"]["nickname"]
		self.assertNotIn("prompt", get_public_state(self.pin)["view"])
		self.assertTrue(get_player_state(self.pin, self.token(artist))["view"]["prompt"])
		guesser = next(n for n in self.players if n != artist)
		submit_action(
			self.pin,
			self.token(artist),
			"stroke_batch",
			str(uuid.uuid4()),
			{"strokes": [{"x1": 0.1, "y1": 0.2, "x2": 0.3, "y2": 0.4}]},
		)
		self.assertEqual(len(get_public_state(self.pin)["view"]["strokes"]), 1)
		self.assertEqual(frappe.db.count("GP Action", {"session": self.session}), 0)
		answer = get_player_state(self.pin, self.token(artist))["view"]["prompt"]
		result = submit_action(self.pin, self.token(guesser), "guess", str(uuid.uuid4()), {"guess": answer})
		self.assertTrue(result["correct"])
		self.advance()
		self.assertEqual(get_host_state(self.session)["phase"], "draw_reveal")
		self.assertGreater(frappe.db.count("GP Score Event", {"session": self.session}), 0)

	def test_bad_strokes_and_artist_guess_are_rejected(self):
		artist = get_host_state(self.session)["view"]["artist"]["nickname"]
		with self.assertRaises(frappe.ValidationError):
			submit_action(
				self.pin,
				self.token(artist),
				"stroke_batch",
				"bad",
				{"strokes": [{"x1": -1, "y1": 0, "x2": 1, "y2": 1}]},
			)
		with self.assertRaises(frappe.ValidationError):
			submit_action(self.pin, self.token(artist), "guess", "artist-guess", {"guess": "rocket"})
