"""One GatherPlay lobby or live game. Hot state lives in Redis; this row is the record."""

import frappe
from frappe.model.document import Document


class GPSession(Document):
	def before_insert(self):
		self.configuration = frappe.parse_json(self.configuration) or {}
		from quizzly import batches
		from quizzly.games import GameContext, get_game_module

		requested = self.configuration.get("rounds")
		config = get_game_module(self.game_key).validate_configuration(
			GameContext(session="", pin="", game_key=self.game_key, configuration=self.configuration),
			self.configuration,
		)
		config["auto_progress"] = self.configuration.get("auto_progress", False)
		self.configuration = config
		self.play_batch = batches.prepare(self.game_key, config, requested)
		if self.play_batch:
			self.configuration["rounds"] = len(self.play_batch["selected"])
		self.next_session = None

	def validate(self):
		from quizzly.batches import protect_session

		protect_session(self)
