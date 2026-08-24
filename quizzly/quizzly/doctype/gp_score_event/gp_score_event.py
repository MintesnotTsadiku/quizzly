"""Immutable ledger entry. Corrections are compensating events, never edits."""

import frappe
from frappe.model.document import Document


class GPScoreEvent(Document):
	pass


def on_doctype_update():
	# the ledger's final word on double-apply: a retried resolve lands twice in Redis
	# pre-checks but only once here
	frappe.db.add_unique("GP Score Event", ["session", "idempotency_key"])
