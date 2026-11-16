"""Who sees the Quizzly tile on the apps screen."""

import frappe


def has_app_permission() -> bool:
	"""Hosts who can read quizzes see the tile and the Quizzly dock."""
	return frappe.has_permission("QZ Quiz", "read")
