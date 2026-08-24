"""One GatherPlay lobby or live game. Hot state lives in Redis; this row is the record."""

import frappe
from frappe.model.document import Document


class GPSession(Document):
	def before_insert(self):
		self.configuration = frappe.parse_json(self.configuration) or {}
