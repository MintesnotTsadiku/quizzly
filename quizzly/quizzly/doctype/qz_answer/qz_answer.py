import frappe
from frappe.model.document import Document


class QZAnswer(Document):
	pass


def on_doctype_update():
	# Duplicate submits die at the DB level regardless of race conditions
	frappe.db.add_unique("QZ Answer", ["participant", "question_row"])
