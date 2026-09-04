import unittest
from unittest.mock import patch
from quizzly.branding import get_application_branding

class SharedBrandingTests(unittest.TestCase):
    def test_standalone_does_not_import_cms(self):
        with patch('frappe.get_installed_apps', return_value=['frappe','quizzly']), patch('frappe.get_attr') as load:
            self.assertEqual(get_application_branding(), {'shared': False})
            load.assert_not_called()

    def test_installed_cms_is_the_single_configuration_source(self):
        config={'branding':{'short_name':'Church'},'theme':{'name':'Shared'}}
        with patch('frappe.get_installed_apps', return_value=['frappe','quizzly','church_management_system']), patch('frappe.get_attr') as load:
            load.return_value.return_value=config
            self.assertEqual(get_application_branding(), {'shared':True,'configuration':config})
            load.assert_called_once_with('church_management_system.api.branding.get_application_branding')
