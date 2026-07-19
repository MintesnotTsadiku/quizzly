import frappe


def get_context(context):
	context.no_cache = 1
	context.boot = {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"site_name": frappe.local.site,
	}
