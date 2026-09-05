import frappe
from frappe.model.document import Document


class GPGamePack(Document):
	def validate(self):
		if self.is_demo and not getattr(self.flags, "in_demo_seed", False) and not self.is_new():
			frappe.throw("Demo packs are read-only. Duplicate this pack to customize it.")

		if not self.flags.in_demo_seed:
			from quizzly.games.round_games.content import validate_items

			validate_items(self.game_key, self.items)
