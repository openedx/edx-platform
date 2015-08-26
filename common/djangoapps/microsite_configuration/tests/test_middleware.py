# -*- coding: utf-8 -*-
"""
Test Microsite middleware.
"""
from mock import patch

from django.test import TestCase
from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings
import unittest


# NOTE: We set SESSION_SAVE_EVERY_REQUEST to True in order to make sure
# Sessions are always started on every request
@override_settings(SESSION_SAVE_EVERY_REQUEST=True)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class MicroSiteSessionCookieTests(TestCase):
    """
    Tests regarding the session cookie management in the middlware for MicroSites
    """

    def setUp(self):
        super(MicroSiteSessionCookieTests, self).setUp()
        # create a test client
        self.client = Client()

    def test_session_cookie_domain_no_microsite(self):
        """
        Tests that non-microsite behaves according to default behavior
        """

        response = self.client.get('/')
        self.assertNotIn('test_microsite.localhost', str(getattr(response, 'cookies')['sessionid']))
        self.assertNotIn('Domain', str(getattr(response, 'cookies')['sessionid']))

    def test_session_cookie_domain(self):
        """
        Makes sure that the cookie being set in a Microsite
        is the one specially overridden in configuration,
        in this case in test.py
        """

        response = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertIn('test_microsite.localhost', str(getattr(response, 'cookies')['sessionid']))

    @patch.dict("django.conf.settings.MICROSITE_CONFIGURATION", {'test_microsite': {'SESSION_COOKIE_DOMAIN': None}})
    def test_microsite_none_cookie_domain(self):
        """
        Tests to make sure that a Microsite that specifies None for 'SESSION_COOKIE_DOMAIN' does not
        set a domain on the session cookie
        """

        response = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertNotIn('test_microsite.localhost', str(getattr(response, 'cookies')['sessionid']))
        self.assertNotIn('Domain', str(getattr(response, 'cookies')['sessionid']))
