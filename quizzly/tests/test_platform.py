import time
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from quizzly.api import generate_game_pin, hash_token
from quizzly.games import engine as gpe
from quizzly.games import get_game_module
from quizzly.games.api import (
	as_dict,
	create_session,
	get_public_state,
	join_session,
	list_public_decks,
	submit_action,
)


class TestRegistry(IntegrationTestCase):
	def test_create_session_is_an_authenticated_whitelisted_method(self):
		frappe.set_user("Administrator")
		frappe.is_whitelisted(create_session)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			frappe.is_whitelisted(create_session)

	def test_browser_json_object_arguments_are_normalized(self):
		self.assertEqual(as_dict('{"seconds": 30}'), {"seconds": 30})
		self.assertEqual(as_dict({"seconds": 30}), {"seconds": 30})
		self.assertEqual(as_dict(None), {})
		with self.assertRaises(frappe.ValidationError):
			as_dict('["not", "an", "object"]')

	def test_registered_modules_expose_manifests(self):
		from quizzly.games import manifests

		keys = {m.key for m in manifests()}
		self.assertIn("quiz", keys)
		self.assertIn("cuecast", keys)

	def test_unknown_game_key_throws(self):
		with self.assertRaises(frappe.ValidationError):
			get_game_module("nope")

	def test_non_module_path_rejected(self):
		from quizzly.games import load_module

		with self.assertRaises((TypeError, AttributeError, ImportError)):
			load_module("quizzly.games.engine.apply_transition")


class TestPublicContentDiscovery(IntegrationTestCase):
	def test_demo_pack_includes_safe_prompt_preview(self):
		pack = frappe.get_doc(
			{
				"doctype": "GP Crowd Pack",
				"title": "Previewable Compass",
				"is_demo": 1,
				"demo_key": "test-previewable-compass",
				"prompts": [
					{
						"prompt_text": "Pick a gathering spot",
						"choice_1": "Garden",
						"choice_2": "Kitchen",
					}
				],
			}
		).insert()
		try:
			preview = next(row for row in list_public_decks("crowd-compass") if row.name == pack.name)
			self.assertEqual(preview.prompt_count, 1)
			self.assertEqual(
				preview.prompts,
				[{"text": "Pick a gathering spot", "choices": ["Garden", "Kitchen"]}],
			)
		finally:
			frappe.delete_doc("GP Crowd Pack", pack.name, force=True, ignore_permissions=True)

	def test_demo_quiz_includes_safe_question_preview(self):
		quiz = frappe.get_doc(
			{
				"doctype": "QZ Quiz",
				"title": "Previewable Quiz",
				"is_demo": 1,
				"demo_key": "test-previewable-quiz",
				"questions": [
					{
						"question_text": "Which answer is safe to show?",
						"option_1": "One",
						"option_2": "Two",
						"option_3": "Three",
						"option_4": "Four",
						"correct_option": "2",
					}
				],
			}
		).insert()
		try:
			preview = next(row for row in list_public_decks("quiz") if row.name == quiz.name)
			self.assertEqual(preview.prompt_count, 1)
			self.assertEqual(
				preview.prompts,
				[{"text": "Which answer is safe to show?", "choices": ["One", "Two", "Three", "Four"]}],
			)
			self.assertNotIn("correct_option", preview.prompts[0])
		finally:
			frappe.db.set_value("QZ Quiz", quiz.name, "is_demo", 0)
			frappe.delete_doc("QZ Quiz", quiz.name, force=True, ignore_permissions=True)


class PlatformTestCase(IntegrationTestCase):
	"""Deck + lobby + two joined players, torn down completely."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.deck = frappe.get_doc(
			{
				"doctype": "GP Cue Deck",
				"title": "Platform Deck",
				"mode": "Act",
				"prompts": [{"prompt_text": t} for t in ["alpha", "bravo", "charlie"]],
			}
		).insert()
		frappe.db.commit()
		created = create_session("cuecast", {"deck": self.deck.name, "seconds": 30})
		self.session = created["session"]
		self.pin = created["game_pin"]
		self.players = {n: join_session(self.pin, n) for n in ["ada", "bob"]}

	def tearDown(self):
		frappe.set_user("Administrator")
		gpe.clear_state(self.session)
		frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY, self.session)
		for dt in ("GP Score Event", "GP Action", "GP Round", "GP Team Membership"):
			for name in frappe.get_all(dt, filters={"session": self.session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		for dt in ("GP Participant", "GP Team"):
			for name in frappe.get_all(dt, filters={"session": self.session}, pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Session", self.session, force=True, ignore_permissions=True)
		frappe.delete_doc("GP Cue Deck", self.deck.name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def activate(self):
		frappe.db.set_value("GP Session", self.session, "status", "Active")

	def open_turn_state(self):
		now = time.time()
		gpe.set_state(
			self.session,
			{
				"schema_version": 1,
				"game_key": "cuecast",
				"session_status": "Active",
				"phase": "turn_open",
				"version": 5,
				"deadline_ts": now + 60,
				"next_ts": now + 60,
				"module_state": {
					"round_index": 0,
					"round_key": "turn-1",
					"actor_team": None,
					"actor_participant": self.players["ada"]["participant"],
					"prompt_ids": [p.name for p in self.deck.prompts],
					"prompt_pos": 1,
					"turn_start_pos": 0,
				},
			},
			ttl=120,
		)
		gpe.open_round_row(
			self.session,
			{"round_index": 0, "round_key": "turn-1", "actor_team": None, "actor_participant": None},
			now + 60,
		)


class TestJoinGauntlet(PlatformTestCase):
	def test_token_stored_hashed_only(self):
		participant = self.players["ada"]["participant"]
		row = frappe.db.get_value("GP Participant", participant, ["token_hash", "nickname"], as_dict=True)
		self.assertEqual(row.token_hash, hash_token(self.players["ada"]["participant_token"]))
		self.assertNotIn(self.players["ada"]["participant_token"], row.token_hash)

	def test_duplicate_nickname_rejected(self):
		with self.assertRaises(frappe.DuplicateEntryError):
			join_session(self.pin, "ada")

	def test_locked_lobby_rejects_join(self):
		frappe.db.set_value("GP Session", self.session, "lobby_locked", 1)
		with self.assertRaises(frappe.ValidationError):
			join_session(self.pin, "cara")

	def test_kicked_token_rejected_everywhere(self):
		participant = self.players["bob"]["participant"]
		frappe.db.set_value("GP Participant", participant, "status", "Kicked")
		self.activate()
		self.open_turn_state()
		with self.assertRaises(frappe.PermissionError):
			submit_action(
				self.pin, self.players["bob"]["participant_token"], "correct_prompt", str(uuid.uuid4())
			)


class TestSubmitGauntlet(PlatformTestCase):
	def setUp(self):
		super().setUp()
		self.activate()
		self.open_turn_state()

	def submit(self, nick="ada", action_type="correct_prompt", key=None):
		return submit_action(
			self.pin, self.players[nick]["participant_token"], action_type, key or str(uuid.uuid4())
		)

	def test_action_persists_with_idempotency(self):
		key = str(uuid.uuid4())
		self.submit(key=key)
		self.submit(key=key)  # replay collapses
		self.assertEqual(frappe.db.count("GP Action", {"session": self.session, "idempotency_key": key}), 1)

	def test_db_unique_backstops_redis_bypass(self):
		key = str(uuid.uuid4())
		self.submit(key=key)
		# a racing duplicate that beat the redis pre-check dies on the DB constraint
		frappe.cache.delete_value(gpe.acted_key(self.session, key))
		self.submit(key=key)
		self.assertEqual(frappe.db.count("GP Action", {"session": self.session}), 1)

	def test_wrong_role_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.submit(nick="bob")


class TestLedger(PlatformTestCase):
	def test_delta_applies_once_under_retry(self):
		team = frappe.get_doc(
			{"doctype": "GP Team", "session": self.session, "team_name": "Ledger", "color": "ember"}
		).insert(ignore_permissions=True)
		delta = gpe_delta(team.name)
		gpe.apply_deltas(self.session, [delta])
		gpe.apply_deltas(self.session, [delta])  # retried resolve
		self.assertEqual(frappe.db.count("GP Score Event", {"session": self.session}), 1)
		self.assertEqual(frappe.db.get_value("GP Team", team.name, "score"), 1)


def gpe_delta(team):
	from quizzly.games import ScoreDelta

	return ScoreDelta(
		subject_type="Team",
		subject=team,
		points=1,
		category="correct_prompt",
		idempotency_key=f"retry-{team}",
	)


class TestPublicSafety(PlatformTestCase):
	def test_public_snapshot_never_carries_prompt_or_controls(self):
		self.activate()
		state = gpe.get_state(self.session)
		if not state:
			self.open_turn_state()
			state = gpe.get_state(self.session)
		module = get_game_module("cuecast")
		view = module.serialize_public_state(
			gpe.context_for(frappe.get_doc("GP Session", self.session)), state
		)
		public = get_public_state(self.pin)
		blob = str(view) + str(public.get("view") or {})
		self.assertNotIn("prompt_text", blob.lower())


class TestPinAllocation(IntegrationTestCase):
	def test_generated_pin_is_six_digits_and_unique_enough(self):
		pin = generate_game_pin()
		self.assertRegex(pin, r"^\d{6}$")
