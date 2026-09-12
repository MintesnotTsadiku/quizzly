"""One site policy; installed modules and existing rooms are never removed."""

import frappe
from frappe import _

DEFAULT_GAMES = ("quiz", "common-ground", "crowd-compass", "cuecast", "doodle-dash", "sequence-sprint")


def published_keys():
	value = frappe.get_cached_doc("GatherPlay Settings").get("published_games")
	return set(DEFAULT_GAMES if value in (None, "") else frappe.parse_json(value))


def check_published(key):
	if key not in published_keys():
		frappe.throw(
			_("This game is not published on this site. Existing rooms can still finish."),
			frappe.PermissionError,
		)


def validate_policy(value):
	from quizzly.games import registry

	keys = list(DEFAULT_GAMES) if value in (None, "") else frappe.parse_json(value)
	if not isinstance(keys, list) or any(not isinstance(k, str) or k not in registry() for k in keys):
		frappe.throw(_("Choose game formats from the installed registry."))
	return sorted(set(keys))


@frappe.whitelist()
def management() -> dict:
	frappe.only_for("System Manager")
	from quizzly.games import manifests

	published = published_keys()
	return {
		"games": [
			{"key": m.key, "title": m.title, "status": m.status, "published": m.key in published}
			for m in manifests()
		]
	}


@frappe.whitelist(methods=["POST"])
def save(published: list | str) -> dict:
	frappe.only_for("System Manager")
	doc = frappe.get_doc("GatherPlay Settings")
	doc.published_games = frappe.as_json(validate_policy(published))
	doc.save()
	return management()


def initialize():
	"""Persist missing defaults before a first policy write creates a partial Single."""
	stored = frappe.db.get_singles_dict("GatherPlay Settings")
	for field in frappe.get_meta("GatherPlay Settings").fields:
		if field.fieldname not in stored and field.default is not None:
			frappe.db.set_single_value("GatherPlay Settings", field.fieldname, field.default)
	frappe.clear_document_cache("GatherPlay Settings", "GatherPlay Settings")
