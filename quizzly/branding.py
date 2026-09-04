"""Optional shared site branding. Quizzly remains usable without CMS installed."""
import frappe


@frappe.whitelist(allow_guest=True, methods=['GET'])
def get_application_branding() -> dict:
    if 'church_management_system' not in frappe.get_installed_apps():
        return {'shared': False}
    provider = frappe.get_attr('church_management_system.api.branding.get_application_branding')
    return {'shared': True, 'configuration': provider()}
