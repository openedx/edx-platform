"""
    Tests for microsites and comprehensive themes.
"""
import unittest

from django.conf import settings
from django.test import TestCase
from django.contrib.sites.models import Site

from openedx.core.djangoapps.theming.models import SiteTheme


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestComprehensiveThemeLMS(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """
    def __add_site_theme__(self, domain, theme):
        """
        Add a Site and SiteTheme record for the given domain and theme
        Args:
            domain: domain to which attach the new Site
            theme: theme to apply on the new site
        """
        site, __ = Site.objects.get_or_create(domain=domain, name=domain)
        SiteTheme.objects.get_or_create(site=site, theme_dir_name=theme)

    def test_theme_footer(self):
        """
        Test that theme footer is used instead of microsite footer.
        """
        # Add SiteTheme with the same domain name as microsite
        self.__add_site_theme__(domain=settings.MICROSITE_TEST_HOSTNAME, theme="test-theme")

        # Test that requesting on a host, where both theme and microsite is applied
        # theme gets priority over microsite.
        resp = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)
        # This string comes from footer.html of test-theme
        self.assertContains(resp, "This is a footer for test-theme.")

    def test_microsite_footer(self):
        """
        Test that microsite footer is used instead of default theme footer.
        """
        # Test that if theming is enabled but there is no SiteTheme for the current site, then
        # DEFAULT_SITE_THEME does not interfere with microsites
        resp = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)
        # This string comes from footer.html of test_site, which is a microsite
        self.assertContains(resp, "This is a Test Site footer")
