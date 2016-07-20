"""
    Tests for comprehensive themes.
"""
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.contrib import staticfiles

from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestComprehensiveThemeLMS(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeLMS, self).setUp()
        self.user = UserFactory()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    def _login(self):
        """ Log into LMS. """
        self.client.login(username=self.user.username, password='test')

    @with_comprehensive_theme("test-theme")
    def test_footer(self):
        """
        Test that theme footer is used instead of default footer.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # This string comes from header.html of test-theme
        self.assertContains(resp, "This is a footer for test-theme.")

    @with_comprehensive_theme("edx.org")
    def test_account_settings_hide_nav(self):
        """
        Test that theme header doesn't show marketing site links for Account Settings page.
        """
        self._login()

        account_settings_url = reverse('account_settings')
        response = self.client.get(account_settings_url)

        # Verify that the header navigation links are hidden for the edx.org version
        self.assertNotContains(response, "How it Works")
        self.assertNotContains(response, "Find courses")
        self.assertNotContains(response, "Schools & Partners")

    @with_comprehensive_theme("test-theme")
    def test_logo_image(self):
        """
        Test that theme logo is used instead of default logo.
        """
        result = staticfiles.finders.find('test-theme/images/logo.png')
        self.assertEqual(result, settings.TEST_THEME / 'lms/static/images/logo.png')


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeCMS(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeCMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @with_comprehensive_theme("test-theme")
    def test_template_override(self):
        """
        Test that theme templates are used instead of default templates.
        """
        resp = self.client.get('/signin')
        self.assertEqual(resp.status_code, 200)
        # This string comes from login.html of test-theme
        self.assertContains(resp, "Login Page override for test-theme.")


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestComprehensiveThemeDisabledLMS(TestCase):
    """
        Test Sass compilation order and sass overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache.
        """
        super(TestComprehensiveThemeDisabledLMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    def test_logo(self):
        """
        Test that default logo is picked in case of no comprehensive theme.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.REPO_ROOT / 'lms/static/images/logo.png')


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeDisabledCMS(TestCase):
    """
    Test default html, sass and static file when no theme is applied.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeDisabledCMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    def test_template_override(self):
        """
        Test that defaults templates are used when no theme is applied.
        """
        resp = self.client.get('/signin')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Login Page override for test-theme.")
