"""CueCast prompt deck. Integrity lives here so nothing can save an unplayable deck."""

import frappe
from frappe import _
from frappe.model.document import Document


class GPCueDeck(Document):
	def validate(self):
		if not self.prompts:
			frappe.throw(_("A deck needs at least one prompt"))
		for prompt in self.prompts:
			if not (prompt.prompt_text or "").strip():
				frappe.throw(_("Prompts cannot be blank"))
