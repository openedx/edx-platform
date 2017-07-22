"""
    Tests for middleware for comprehensive themes.
"""

from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sites.models import Site
from openedx.core.djangoapps.theming.middleware import CurrentSiteThemeMiddleware
from student.tests.factories import UserFactory

from ..views import set_user_preview_site_theme

TEST_URL = '/test'
TEST_THEME_NAME = 'test-theme'


class TestCurrentSiteThemeMiddleware(TestCase):
    """
    Test theming middleware.
    """
    def setUp(self):
        """
        Initialize middleware and related objects
        """
        super(TestCurrentSiteThemeMiddleware, self).setUp()

        self.site_theme_middleware = CurrentSiteThemeMiddleware()
        self.user = UserFactory.create()

    def create_mock_get_request(self):
        """
        Returns a mock GET request.
        """
        request = RequestFactory().get(TEST_URL)
        self.initialize_mock_request(request)
        return request

    def initialize_mock_request(self, request):
        """
        Initialize a test request.
        """
        request.user = self.user
        request.site, __ = Site.objects.get_or_create(domain='test', name='test')
        request.session = {}
        MessageMiddleware().process_request(request)

    @override_settings(DEFAULT_SITE_THEME=TEST_THEME_NAME)
    def test_default_site_theme(self):
        """
        Test that request.site_theme returns theme defined by DEFAULT_SITE_THEME setting
        when there is no theme associated with the current site.
        """
        request = self.create_mock_get_request()
        self.assertEqual(self.site_theme_middleware.process_request(request), None)
        self.assertIsNotNone(request.site_theme)
        self.assertEqual(request.site_theme.theme_dir_name, TEST_THEME_NAME)

    @override_settings(DEFAULT_SITE_THEME=None)
    def test_default_site_theme_2(self):
        """
        Test that request.site_theme returns None when there is no theme associated with
        the current site and DEFAULT_SITE_THEME is also None.
        """
        request = self.create_mock_get_request()
        self.assertEqual(self.site_theme_middleware.process_request(request), None)
        self.assertIsNone(request.site_theme)

    def test_preview_theme(self):
        """
        Verify that preview themes behaves correctly.
        """
        # First request a preview theme
        post_request = RequestFactory().post('/test')
        self.initialize_mock_request(post_request)
        set_user_preview_site_theme(post_request, TEST_THEME_NAME)

        # Next request a page and verify that the theme is returned
        get_request = self.create_mock_get_request()
        self.assertEqual(self.site_theme_middleware.process_request(get_request), None)
        self.assertEqual(get_request.site_theme.theme_dir_name, TEST_THEME_NAME)

        # Request to reset the theme
        post_request = RequestFactory().post('/test')
        self.initialize_mock_request(post_request)
        set_user_preview_site_theme(post_request, None)

        # Finally verify that no theme is returned
        get_request = self.create_mock_get_request()
        self.assertEqual(self.site_theme_middleware.process_request(get_request), None)
        self.assertIsNone(get_request.site_theme)
