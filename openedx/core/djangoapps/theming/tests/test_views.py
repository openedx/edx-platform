"""
    Tests for comprehensive them
"""


from django.conf import settings
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sites.models import Site
from django.test import TestCase

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from openedx.core.djangoapps.theming.middleware import CurrentSiteThemeMiddleware
from common.djangoapps.student.tests.factories import UserFactory

THEMING_ADMIN_URL = '/theming/admin'
TEST_THEME_NAME = 'test-theme'
TEST_PASSWORD = 'test'


class TestThemingViews(TestCase):
    """
    Test theming views.
    """
    def setUp(self):
        """
        Initialize middleware and related objects
        """
        super(TestThemingViews, self).setUp()

        self.site_theme_middleware = CurrentSiteThemeMiddleware()
        self.user = UserFactory.create()

    def initialize_mock_request(self, request):
        """
        Initialize a test request.
        """
        request.user = self.user
        request.site, __ = Site.objects.get_or_create(domain='test', name='test')
        request.session = {}
        MessageMiddleware().process_request(request)

    def test_preview_theme_access(self):
        """
        Verify that users have the correct access to preview themes.
        """
        # Anonymous users get redirected to the login page
        response = self.client.get(THEMING_ADMIN_URL)
        # Studio login redirects to LMS login
        expected_target_status_code = 200 if settings.ROOT_URLCONF == 'lms.urls' else 302
        self.assertRedirects(
            response,
            '{login_url}?next={url}'.format(
                login_url=settings.LOGIN_URL,
                url=THEMING_ADMIN_URL,
            ),
            target_status_code=expected_target_status_code
        )

        # Logged in non-global staff get a 404
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.client.get(THEMING_ADMIN_URL)
        self.assertEqual(response.status_code, 404)

        # Global staff can access the page
        global_staff = GlobalStaffFactory()
        self.client.login(username=global_staff.username, password=TEST_PASSWORD)
        response = self.client.get(THEMING_ADMIN_URL)
        self.assertEqual(response.status_code, 200)

    def test_preview_theme(self):
        """
        Verify that preview themes behaves correctly.
        """
        global_staff = GlobalStaffFactory()
        self.client.login(username=global_staff.username, password=TEST_PASSWORD)

        # First request a preview theme
        post_response = self.client.post(
            THEMING_ADMIN_URL,
            {
                'action': 'set_preview_theme',
                'preview_theme': TEST_THEME_NAME,
            }
        )
        self.assertRedirects(post_response, THEMING_ADMIN_URL)

        # Next request a page and verify that the correct theme has been chosen
        response = self.client.get(THEMING_ADMIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            u'<option value="{theme_name}" selected=selected>'.format(theme_name=TEST_THEME_NAME)
        )

        # Request to reset the theme
        post_response = self.client.post(
            THEMING_ADMIN_URL,
            {
                'action': 'reset_preview_theme'
            }
        )
        self.assertRedirects(post_response, THEMING_ADMIN_URL)

        # Finally verify that the test theme is no longer selected
        response = self.client.get(THEMING_ADMIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            u'<option value="{theme_name}">'.format(theme_name=TEST_THEME_NAME)
        )
