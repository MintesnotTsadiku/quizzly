from frappe.model.document import Document


class QZSession(Document):
	def before_insert(self):
		from quizzly.batches import prepare

		self.play_batch = prepare("quiz", {"pack": self.quiz}, self.flags.batch_count)
		self.next_session = None

	def validate(self):
		from quizzly.batches import protect_session

		protect_session(self)

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auto_advance: DF.Check
		current_question: DF.Int
		ended_at: DF.Datetime | None
		game_pin: DF.Data | None
		host: DF.Link
		lobby_locked: DF.Check
		quiz: DF.Link
		randomize_answer_order: DF.Check
		started_at: DF.Datetime | None
		status: DF.Literal["Lobby", "Active", "Ended", "Cancelled"]
	# end: auto-generated types
