"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""

from mock import patch

from django.test import TestCase
from django.test.utils import override_settings


class TestFooter(TestCase):

    def test_edx_footer(self):
        """
        Verify that the homepage, when accessed at edx.org, has the edX footer
        """
        with patch.dict('django.conf.settings.FEATURES', {"IS_EDX_DOMAIN": True}):
            resp = self.client.get('/')
            self.assertEqual(resp.status_code, 200)

            # assert that footer template has been properly overridden on homepage
            # test the top-level element class; which is less likely to change than copy.
            self.assertContains(resp, 'edx-footer')

    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """
        with patch.dict('django.conf.settings.FEATURES', {"IS_EDX_DOMAIN": False}):
            resp = self.client.get('/')
            self.assertEqual(resp.status_code, 200)

            # assert that footer template has been properly overridden on homepage
            # test the top-level element class; which is less likely to change than copy.
            self.assertContains(resp, 'wrapper-footer')
