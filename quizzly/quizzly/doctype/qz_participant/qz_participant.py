import frappe
from frappe import _
from frappe.model.document import Document


class QZParticipant(Document):
	def validate(self):
		self.nickname = self.nickname.strip()
		if not self.nickname:
			frappe.throw(_("Nickname is required"))
		# ponytail: exists-check has a race window; a duplicate slipping through is cosmetic
		duplicate = frappe.db.exists(
			"QZ Participant",
			{
				"session": self.session,
				"nickname": self.nickname,
				"kicked": 0,
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			frappe.throw(_("Nickname is already taken"), frappe.DuplicateEntryError)
