import frappe
from frappe.model.document import Document


class GPAction(Document):
	pass


def on_doctype_update():
	"""Retries and double-taps collapse here, whatever races the Redis pre-check loses."""
	frappe.db.add_unique("GP Action", ["session", "participant", "idempotency_key"])
