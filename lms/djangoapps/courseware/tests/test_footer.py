"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""

from django.test import TestCase
from django.test.utils import override_settings


class TestFooter(TestCase):

    @override_settings(SITE_NAME="edx.org")
    def test_edx_footer(self):
        """
        Verify that the homepage, when accessed at edx.org, has the edX footer
        """

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # assert that footer template has been properly overriden on homepage
        self.assertContains(resp, 'EdX is a non-profit created by founding partners Harvard and MIT')

    @override_settings(SITE_NAME="example.com")
    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # assert that footer template has been properly overriden on homepage
        self.assertContains(resp, 'Powered by Open edX')
