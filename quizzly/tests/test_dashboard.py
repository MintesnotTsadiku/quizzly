import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from quizzly.dashboard import get_host_dashboard


class TestHostDashboard(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.host = frappe.get_doc(
			{
				"doctype": "User",
				"email": "dashboard-host@example.com",
				"first_name": "Dashboard Host",
				"send_welcome_email": 0,
				"roles": [{"role": "Quiz Host"}],
			}
		).insert(ignore_permissions=True)
		self.quiz = frappe.get_doc(
			{
				"doctype": "QZ Quiz",
				"title": "Dashboard Quiz",
				"questions": [
					{
						"question_text": "Ready?",
						"option_1": "One",
						"option_2": "Two",
						"option_3": "Three",
						"option_4": "Four",
						"correct_option": "1",
					}
				],
			}
		).insert()
		self.quiz_session = frappe.get_doc(
			{
				"doctype": "QZ Session",
				"quiz": self.quiz.name,
				"host": self.host.name,
				"game_pin": "731001",
				"status": "Ended",
				"started_at": now_datetime(),
				"ended_at": now_datetime(),
			}
		).insert()
		self.gp_session = frappe.get_doc(
			{
				"doctype": "GP Session",
				"game_key": "cuecast",
				"host": self.host.name,
				"game_pin": "731002",
				"status": "Active",
				"started_at": now_datetime(),
			}
		).insert()
		for nickname in ("Hana", "Dawit"):
			frappe.get_doc(
				{
					"doctype": "QZ Participant",
					"session": self.quiz_session.name,
					"nickname": nickname,
				}
			).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "GP Participant",
				"session": self.gp_session.name,
				"nickname": "Selam",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_combines_active_history_and_analytics_for_the_host(self):
		frappe.set_user(self.host.name)

		dashboard = get_host_dashboard()

		self.assertEqual(dashboard["summary"]["total_sessions"], 2)
		self.assertEqual(dashboard["summary"]["active_sessions"], 1)
		self.assertEqual(dashboard["summary"]["completed_sessions"], 1)
		self.assertEqual(dashboard["summary"]["total_players"], 3)
		self.assertEqual({row["game_title"] for row in dashboard["sessions"]}, {"Dashboard Quiz", "CueCast"})
		self.assertEqual({row["pin"] for row in dashboard["sessions"]}, {"731001", "731002"})
		active = next(row for row in dashboard["sessions"] if row["pin"] == "731002")
		completed = next(row for row in dashboard["sessions"] if row["pin"] == "731001")
		self.assertTrue(active["is_active"])
		self.assertTrue(active["can_open"])
		self.assertFalse(completed["is_active"])
