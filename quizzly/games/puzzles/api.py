"""Stateless practice: replay a small public move list through the real rules."""

import frappe
from frappe.rate_limiter import rate_limit

from .rules import KEYS, apply, initial


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60)
def practice(game_key: str, actions: list | str | None = None) -> dict:
	if game_key not in KEYS:
		frappe.throw("Unknown puzzle")
	actions = frappe.parse_json(actions) if isinstance(actions, str) else actions
	if not isinstance(actions, list) or len(actions) > 128:
		frappe.throw("Reset the practice board to keep playing.")
	if len(frappe.as_json(actions)) > 20000:
		frappe.throw("Practice move list is too large.")
	state = initial(game_key)
	try:
		for move in actions:
			if not isinstance(move, dict) or not isinstance(move.get("payload"), dict):
				raise ValueError("Choose a board move.")
			state = apply(state, move.get("action"), move["payload"])
	except (ValueError, TypeError, KeyError) as e:
		frappe.throw(str(e))
	return state
