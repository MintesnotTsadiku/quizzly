import frappe
from frappe.model.document import Document
from frappe.utils import add_days, now_datetime


class GatherPlayReceipt(Document):
	def validate(self):
		if self.is_new():
			return
		old = self.get_doc_before_save()
		if old.status == self.status:
			return
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only a site administrator can review receipts.", frappe.PermissionError)
		if self.status not in ("Approved", "Rejected"):
			frappe.throw("Review a receipt by approving or rejecting it.")
		if self.status == "Rejected" and not (self.review_note or "").strip():
			frappe.throw("Add a reason so the account holder understands the decision.")
		from quizzly.access import settings

		self.valid_until = (
			add_days(now_datetime(), settings().plan_days) if self.status == "Approved" else now_datetime()
		)
		self.reviewed_by, self.reviewed_at = frappe.session.user, now_datetime()
