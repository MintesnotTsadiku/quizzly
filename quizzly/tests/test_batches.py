import uuid

import frappe
from frappe.tests import IntegrationTestCase

from quizzly import batches, publishing
from quizzly.api import create_session as create_quiz
from quizzly.api import hash_token
from quizzly.games.api import create_session, list_games


class TestBatches(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		publishing.initialize()
		self.policy = frappe.db.get_single_value("GatherPlay Settings", "published_games")
		self.set_policy(list(publishing.DEFAULT_GAMES))
		self.quiz = frappe.get_doc(
			{
				"doctype": "QZ Quiz",
				"title": "Batch test " + uuid.uuid4().hex,
				"is_demo": 0,
				"questions": [
					{
						"question_text": f"Question {i}",
						"option_1": "Yes",
						"option_2": "No",
						"option_3": "Maybe",
						"option_4": "Later",
						"correct_option": "1",
					}
					for i in range(40)
				],
			}
		).insert()
		self.created = []

	def set_policy(self, keys):
		frappe.db.set_single_value("GatherPlay Settings", "published_games", frappe.as_json(keys))
		frappe.clear_document_cache("GatherPlay Settings", "GatherPlay Settings")

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, name in reversed(self.created):
			for child in (
				["QZ Participant", "QZ Answer"]
				if dt == "QZ Session"
				else ["GP Participant", "GP Round", "GP Score Event", "GP Team"]
			):
				frappe.db.delete(child, {"session": name})
			frappe.db.delete(dt, {"name": name})
		frappe.delete_doc("QZ Quiz", self.quiz.name, force=True)
		frappe.db.set_single_value("GatherPlay Settings", "published_games", self.policy)
		frappe.clear_document_cache("GatherPlay Settings", "GatherPlay Settings")
		frappe.db.commit()

	def room(self, count=10):
		created = create_quiz(self.quiz.name, count)
		self.created.append(("QZ Session", created["session"]))
		return frappe.get_doc("QZ Session", created["session"])

	def ended(self, doc, seen=None):
		batches.note_seen(doc, seen if seen is not None else batches.batch_of(doc)["selected"])
		frappe.db.set_value(doc.doctype, doc.name, "status", "Ended")
		doc.reload()

	def next(self, doc, reset=False):
		created = batches.replay(doc.name, quiz=True, reset=reset)
		if ("QZ Session", created["session"]) not in self.created:
			self.created.append(("QZ Session", created["session"]))
		return frappe.get_doc("QZ Session", created["session"])

	def test_selection_is_durable_and_replay_exhausts_without_repeats(self):
		from quizzly.engine import get_quiz_questions

		doc = self.room()
		seen = set()
		for index in range(4):
			selected = batches.batch_of(doc)["selected"]
			self.assertEqual(len(set(selected)), 10)
			self.assertFalse(seen & set(selected))
			self.assertEqual([q.name for q in get_quiz_questions(doc)], selected)
			doc.reload()
			self.assertEqual(batches.batch_of(doc)["selected"], selected)
			seen.update(selected)
			self.ended(doc)
			if index < 3:
				doc = self.next(doc)
		self.assertEqual(batches.summary(doc)["remaining"], 0)
		with self.assertRaises(frappe.ValidationError):
			self.next(doc)
		reset = self.next(doc, reset=True)
		self.assertEqual(len(batches.batch_of(reset)["selected"]), 10)
		self.assertEqual(batches.batch_of(reset)["used"], [])

	def test_partial_batch_preserves_requested_size_and_retries_return_same_room(self):
		doc = self.room(30)
		self.ended(doc)
		next_doc = self.next(doc)
		self.assertEqual(batches.batch_of(next_doc)["requested"], 30)
		self.assertEqual(len(batches.batch_of(next_doc)["selected"]), 10)
		self.assertEqual(self.next(doc).name, next_doc.name)
		self.ended(next_doc)
		self.assertEqual(len(batches.batch_of(self.next(next_doc, reset=True))["selected"]), 30)

	def test_unseen_reserved_content_remains_available_and_groups_are_independent(self):
		doc = self.room(10)
		first = batches.batch_of(doc)["selected"][0]
		self.ended(doc, [first])
		next_doc = self.next(doc)
		self.assertEqual(batches.batch_of(next_doc)["used"], [first])
		self.assertNotIn(first, batches.batch_of(next_doc)["selected"])
		other = self.room(40)
		self.assertEqual(len(batches.batch_of(other)["selected"]), 40)

	def test_bad_counts_are_rejected(self):
		for value in (-1, 41, 1.5, "garbage"):
			with (
				self.subTest(value=value),
				self.assertRaises((frappe.ValidationError, frappe.FrappeTypeError)),
			):
				self.room(value)

	def test_history_and_identity_cannot_be_overwritten_through_document_save(self):
		doc = self.room()
		doc.play_batch = {"selected": []}
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_replay_requires_owner_and_an_ended_room(self):
		doc = self.room()
		with self.assertRaises(frappe.ValidationError):
			self.next(doc)
		self.ended(doc)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			batches.replay(doc.name, quiz=True)

	def test_pack_language_change_requires_explicit_reset(self):
		doc = self.room()
		self.ended(doc)
		frappe.db.set_value("QZ Quiz", self.quiz.name, "content_language", "am")
		self.assertTrue(batches.summary(doc)["scope_changed"])
		with self.assertRaises(frappe.ValidationError):
			self.next(doc)
		self.assertEqual(batches.batch_of(self.next(doc, reset=True))["scope"][-1], "am")

	def test_player_tokens_transfer_but_kicked_players_do_not(self):
		doc = self.room()
		for nickname, kicked in (("Included", 0), ("Removed", 1)):
			frappe.get_doc(
				{
					"doctype": "QZ Participant",
					"session": doc.name,
					"nickname": nickname,
					"token_hash": hash_token(nickname),
					"kicked": kicked,
				}
			).insert(ignore_permissions=True)
		self.ended(doc)
		next_doc = self.next(doc)
		self.assertEqual(frappe.db.count("QZ Participant", {"session": next_doc.name}), 1)
		self.assertEqual(
			frappe.db.get_value("QZ Participant", {"session": next_doc.name}, "token_hash"),
			hash_token("Included"),
		)

	def test_policy_is_shared_by_catalog_api_and_document_creation(self):
		self.assertEqual({g["key"] for g in list_games()}, set(publishing.DEFAULT_GAMES))
		doc = self.room()
		self.set_policy([])
		self.assertEqual(list_games(), [])
		with self.assertRaises(frappe.PermissionError):
			create_quiz(self.quiz.name)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				{"doctype": "QZ Session", "quiz": self.quiz.name, "host": "Administrator"}
			).insert()
		self.assertEqual(batches.batch_of(doc)["selected"], batches.batch_of(doc.reload())["selected"])
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			publishing.save(list(publishing.DEFAULT_GAMES))

	def test_management_can_publish_nothing_and_reject_unknown_keys(self):
		publishing.save([])
		self.assertEqual(list_games(), [])
		with self.assertRaises(frappe.ValidationError):
			publishing.save(["uninstalled-game"])

	def test_administrator_ui_allowance_matches_existing_creation_exemption(self):
		from quizzly.access import allowance

		self.assertEqual(allowance(None, "hosts"), (None, ""))

	def test_common_ground_uses_three_then_two_prompts(self):
		created = create_session("common-ground", {"pack": "everyday", "rounds": 3, "language": "am"})
		doc = frappe.get_doc("GP Session", created["session"])
		self.created.append((doc.doctype, doc.name))
		self.ended(doc)
		created = batches.replay(doc.name)
		next_doc = frappe.get_doc("GP Session", created["session"])
		self.created.append((next_doc.doctype, next_doc.name))
		self.assertEqual(len(batches.batch_of(next_doc)["selected"]), 2)
		self.assertEqual(frappe.parse_json(next_doc.configuration)["rounds"], 2)
		self.assertFalse(set(batches.batch_of(doc)["selected"]) & set(batches.batch_of(next_doc)["selected"]))
