import frappe

from quizzly.avatars import get_boot_pack
from quizzly.nicknames import get_boot_words


def get_context(context):
	context.no_cache = 1
	context.boot = {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"site_name": frappe.local.site,
		"socketio_port": frappe.conf.get("socketio_port"),
		"session_user": frappe.session.user,
		"avatar_pack": get_boot_pack(),
		"nickname_words": get_boot_words(),
	}
