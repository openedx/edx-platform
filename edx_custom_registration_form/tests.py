import unittest
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from .forms import PhoneInfoForm


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@override_settings(REGISTRATION_EXTENSION_FORM='reg_form_ext.forms.PhoneInfoForm')
class PhoneFormTest(TestCase):
    """Test the registration extension for phone numbers"""

    def setUp(self):
        super(PhoneFormTest, self).setUp()
        self.client = Client()

    def test_phone_info_form(self):
        """Ensure that form is rendered to registration page"""
        response = self.client.get(reverse('register_user'))
        self.assertContains(response, "Country Calling Code")
        self.assertContains(response, "Phone Number")

    def test_phone_form_handler(self):
        """Ensure that form properly accepts test data"""
        form_data = {"country_code": "1", "phone_number": "206-555-5555"}
        form = PhoneInfoForm(data=form_data)
        self.assertTrue(form.is_valid())
