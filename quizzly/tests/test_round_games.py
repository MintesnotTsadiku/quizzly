import time,uuid
import frappe
from frappe.tests import IntegrationTestCase
from quizzly.games import manifests
from quizzly.games import engine as gpe
from quizzly.games.api import create_session,get_host_state,get_public_state,join_session,start_session,submit_action
from quizzly.demo.seed import ROUND_DEMO_TITLES


class TestRoundGameCatalog(IntegrationTestCase):
	def setUp(self): frappe.set_user("Administrator")
	def test_every_planned_game_is_registered_and_has_exactly_three_demos(self):
		available={m.key for m in manifests() if m.status=="Available"}
		self.assertTrue(set(ROUND_DEMO_TITLES).issubset(available))
		for key in ROUND_DEMO_TITLES:
			self.assertEqual(frappe.db.count("GP Game Pack",{"game_key":key,"is_demo":1}),3,key)

	def test_numeric_round_is_secret_scored_and_reconnectable(self):
		pack=frappe.db.get_value("GP Game Pack",{"game_key":"closest-call","is_demo":1})
		created=create_session("closest-call",{"pack":pack,"seconds":15,"rounds":1});session,pin=created["session"],created["game_pin"]
		players={n:join_session(pin,n) for n in ("Marta","Samuel","Yonas")};start_session(session);frappe.db.commit()
		try:
			public=get_public_state(pin);self.assertEqual(public["phase"],"round_open");self.assertNotIn("target",public["view"]);self.assertNotIn("answer",public["view"])
			for n,value in zip(players,(9,12,40),strict=True):submit_action(pin,players[n]["participant_token"],"submit",str(uuid.uuid4()),{"value":value})
			state=gpe.get_state(session);state["next_ts"]=time.time()-1;state["deadline_ts"]=state["next_ts"];gpe.set_state(session,state,ttl=120);gpe.tick_once()
			self.assertEqual(get_host_state(session)["phase"],"round_reveal");self.assertEqual(frappe.db.count("GP Score Event",{"session":session}),3)
		finally:
			gpe.clear_state(session);frappe.cache.srem(gpe.ACTIVE_SESSIONS_KEY,session)
			for dt in ("GP Score Event","GP Action","GP Round","GP Team Membership","GP Participant","GP Team"):
				for name in frappe.get_all(dt,filters={"session":session},pluck="name"):frappe.delete_doc(dt,name,force=True,ignore_permissions=True)
			frappe.delete_doc("GP Session",session,force=True,ignore_permissions=True);frappe.db.commit()
