"""
Tests for microsite admin
"""
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from microsite_configuration.admin import MicrositeAdmin
from microsite_configuration.models import Microsite
from microsite_configuration.tests.tests import DatabaseMicrositeTestCase


class MicrositeAdminTests(DatabaseMicrositeTestCase):
    """
    Test class for MicrositeAdmin
    """

    def setUp(self):
        super(MicrositeAdminTests, self).setUp()
        self.adminsite = AdminSite()
        self.microsite_admin = MicrositeAdmin(Microsite, self.adminsite)
        self.request = HttpRequest()

    def test_fields_in_admin_form(self):
        """
        Tests presence of form fields for Microsite.
        """
        microsite_form = self.microsite_admin.get_form(self.request, self.microsite)
        self.assertEqual(
            list(microsite_form.base_fields),
            ["site", "key", "values"]
        )

    def test_save_action_admin_form(self):
        """
        Tests save action for Microsite model form.
        """
        new_values = {
            "domain_prefix": "testmicrosite_new",
            "platform_name": "Test Microsite New"
        }
        microsite_form = self.microsite_admin.get_form(self.request)(instance=self.microsite, data={
            "key": self.microsite.key,
            "site": self.microsite.site.id,
            "values": new_values,
        })
        self.assertTrue(microsite_form.is_valid())
        microsite_form.save()
        new_microsite = Microsite.objects.get(key=self.microsite.key)
        self.assertEqual(new_microsite.values, new_values)
