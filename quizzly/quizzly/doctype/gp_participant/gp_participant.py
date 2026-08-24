import frappe
from frappe import _
from frappe.model.document import Document

from quizzly.avatars import default_avatar, is_valid_avatar


class GPParticipant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		avatar: DF.Data | None
		joined_at: DF.Datetime | None
		nickname: DF.Data
		rank: DF.Int | None
		role: DF.Literal["Player", "Captain", "Performer", "Spectator", "Assistant Moderator"]
		score: DF.Int
		session: DF.Link
		status: DF.Literal["Active", "Disconnected", "Benched", "Eliminated", "Kicked"]
		team: DF.Link | None
		token_hash: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.nickname = (self.nickname or "").strip()
		if not self.nickname:
			frappe.throw(_("Nickname is required"))
		self.validate_avatar()

	def validate_avatar(self):
		if not self.avatar:
			self.avatar = default_avatar(self.nickname)
		elif not is_valid_avatar(self.avatar):
			# rejected, not defaulted: a silent fallback hides a stale client
			frappe.throw(_("Unknown avatar {0}").format(self.avatar))
