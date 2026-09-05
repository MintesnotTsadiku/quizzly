import re

import frappe
from frappe.model.document import Document


class GatherPlaySettings(Document):
	def validate(self):
		if self.default_language not in ("en", "am"):
			frappe.throw("Choose English (en) or Amharic (am).")
		if not re.fullmatch(r"#[0-9a-fA-F]{6}", self.accent_color or ""):
			frappe.throw("Use a six-digit hexadecimal accent color.")
		for field in (
			"guest_host_limit",
			"guest_pack_limit",
			"member_host_limit",
			"member_pack_limit",
			"paid_host_limit",
			"paid_pack_limit",
		):
			if not 0 <= int(self.get(field) or 0) <= 100000:
				frappe.throw("Allowances must be between 0 and 100,000.")
		for field in ("guest_days", "plan_days", "provisional_days"):
			if not 1 <= int(self.get(field) or 0) <= 365:
				frappe.throw("Validity must be between 1 and 365 days.")
		if self.provisional_days > self.plan_days:
			frappe.throw("Provisional access cannot outlast the plan.")
		if self.access_mode == "Paid" and (
			not self.price or self.price <= 0 or not self.payment_instructions
		):
			frappe.throw("Set a positive price and payment instructions before enabling paid access.")
		if not re.fullmatch(r"[A-Z]{3}", self.currency or ""):
			frappe.throw("Use a three-letter currency code, such as ETB.")
		if self.logo and not self.logo.startswith(("/files/", "/assets/")):
			frappe.throw("Use a public image hosted on this site for the logo.")
