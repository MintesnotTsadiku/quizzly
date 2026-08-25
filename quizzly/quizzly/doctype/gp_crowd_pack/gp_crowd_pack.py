"""Crowd Compass poll pack. Integrity lives here so nothing can save an unplayable pack."""

import frappe
from frappe import _
from frappe.model.document import Document


class GPCrowdPack(Document):
	def validate(self):
		if not self.prompts:
			frappe.throw(_("A pack needs at least one prompt"))
		for prompt in self.prompts:
			if not (prompt.prompt_text or "").strip():
				frappe.throw(_("Prompts cannot be blank"))
			choices = [c for c in (prompt.choice_1, prompt.choice_2, prompt.choice_3, prompt.choice_4) if (c or "").strip()]
			if len(choices) < 2:
				frappe.throw(_("Every prompt needs at least two choices"))
