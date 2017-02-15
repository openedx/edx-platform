"""
    Tests for middleware for comprehensive themes.
"""
from mock import Mock
from django.test import TestCase, override_settings
from django.contrib.sites.models import Site

from openedx.core.djangoapps.theming.middleware import CurrentSiteThemeMiddleware


class TestCurrentSiteThemeMiddlewareLMS(TestCase):
    """
    Test theming middleware.
    """
    def setUp(self):
        """
        Initialize middleware and related objects
        """
        super(TestCurrentSiteThemeMiddlewareLMS, self).setUp()

        self.site_theme_middleware = CurrentSiteThemeMiddleware()
        self.request = Mock()
        self.request.site, __ = Site.objects.get_or_create(domain="test", name="test")
        self.request.session = {}

    @override_settings(DEFAULT_SITE_THEME="test-theme")
    def test_default_site_theme(self):
        """
        Test that request.site_theme returns theme defined by DEFAULT_SITE_THEME setting
        when there is no theme associated with the current site.
        """
        self.assertEqual(self.site_theme_middleware.process_request(self.request), None)
        self.assertIsNotNone(self.request.site_theme)
        self.assertEqual(self.request.site_theme.theme_dir_name, "test-theme")

    @override_settings(DEFAULT_SITE_THEME=None)
    def test_default_site_theme_2(self):
        """
        Test that request.site_theme returns None when there is no theme associated with
        the current site and DEFAULT_SITE_THEME is also None.
        """
        self.assertEqual(self.site_theme_middleware.process_request(self.request), None)
        self.assertIsNone(self.request.site_theme)
