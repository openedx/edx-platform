"""Tests of comprehensive theming."""
import unittest
import mock

from django.conf import settings
from django.db.transaction import TransactionManagementError
from django.test import TestCase, RequestFactory, override_settings

from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme
from openedx.core.djangoapps.theming.helpers import get_template_path_with_theme, strip_site_theme_templates_path, \
    get_current_site_theme_dir, get_themes, Theme


class TestHelpers(TestCase):
    """Test comprehensive theming helper functions."""

    def test_get_themes(self):
        """
        Tests template paths are returned from enabled theme.
        """
        expected_themes = [
            Theme('red-theme', 'red-theme'),
            Theme('edge.edx.org', 'edge.edx.org'),
            Theme('edx.org', 'edx.org'),
            Theme('stanford-style', 'stanford-style'),
        ]
        actual_themes = get_themes()
        self.assertItemsEqual(expected_themes, actual_themes)

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    def test_get_themes_2(self):
        """
        Tests template paths are returned from enabled theme.
        """
        expected_themes = [
            Theme('test-theme', 'test-theme'),
        ]
        actual_themes = get_themes()
        self.assertItemsEqual(expected_themes, actual_themes)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestHelpersLMS(TestCase):
    """Test comprehensive theming helper functions."""

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('header.html')
        self.assertEqual(template_path, '/red-theme/lms/templates/header.html')

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_for_missing_template(self):
        """
        Tests default template paths are returned if template is not found in the theme.
        """
        template_path = get_template_path_with_theme('course.html')
        self.assertEqual(template_path, 'course.html')

    def test_get_template_path_with_theme_disabled(self):
        """
        Tests default template paths are returned when theme is non theme is enabled.
        """
        template_path = get_template_path_with_theme('header.html')
        self.assertEqual(template_path, 'header.html')

    @with_comprehensive_theme('red-theme')
    def test_strip_site_theme_templates_path_theme_enabled(self):
        """
        Tests site theme templates path is stripped from the given template path.
        """
        template_path = strip_site_theme_templates_path('/red-theme/lms/templates/header.html')
        self.assertEqual(template_path, 'header.html')

    def test_strip_site_theme_templates_path_theme_disabled(self):
        """
        Tests site theme templates path returned unchanged if no theme is applied.
        """
        template_path = strip_site_theme_templates_path('/red-theme/lms/templates/header.html')
        self.assertEqual(template_path, '/red-theme/lms/templates/header.html')

    @with_comprehensive_theme('red-theme')
    def test_get_current_site_theme_dir(self):
        """
        Tests current site theme name.
        """
        factory = RequestFactory()
        with mock.patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            current_site = get_current_site_theme_dir()
            self.assertEqual(current_site, 'red-theme')

    @with_comprehensive_theme('red-theme')
    @mock.patch('django.core.cache')
    def test_get_current_site_theme_dir_transaction_exception_scenario(self, mock_cache):
        """
        Confirm that the operation exits gracefully when encountering a TransactionManagementError
        """
        factory = RequestFactory()
        with mock.patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            # Set up the mocked response to get_current_site, which will throw a TransactionManagementError
            with mock.patch(
                'openedx.core.djangoapps.theming.helpers.get_current_site',
                return_value=mock.Mock(**{"themes.first.side_effect": TransactionManagementError}),
            ):
                mock_cache = mock.Mock()
                mock_cache.get.return_value = None

                # The TransactionManagementError should cause get_current_site_theme_dir to return "None"
                theme_dir = get_current_site_theme_dir()
                self.assertIsNone(theme_dir)


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestHelpersCMS(TestCase):
    """Test comprehensive theming helper functions."""

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('login.html')
        self.assertEqual(template_path, '/red-theme/cms/templates/login.html')

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_for_missing_template(self):
        """
        Tests default template paths are returned if template is not found in the theme.
        """
        template_path = get_template_path_with_theme('certificates.html')
        self.assertEqual(template_path, 'certificates.html')

    def test_get_template_path_with_theme_disabled(self):
        """
        Tests default template paths are returned when theme is non theme is enabled.
        """
        template_path = get_template_path_with_theme('login.html')
        self.assertEqual(template_path, 'login.html')

    @with_comprehensive_theme('red-theme')
    def test_strip_site_theme_templates_path_theme_enabled(self):
        """
        Tests site theme templates path is stripped from the given template path.
        """
        template_path = strip_site_theme_templates_path('/red-theme/cms/templates/login.html')
        self.assertEqual(template_path, 'login.html')

    def test_strip_site_theme_templates_path_theme_disabled(self):
        """
        Tests site theme templates path returned unchanged if no theme is applied.
        """
        template_path = strip_site_theme_templates_path('/red-theme/cms/templates/login.html')
        self.assertEqual(template_path, '/red-theme/cms/templates/login.html')

    @with_comprehensive_theme('red-theme')
    def test_get_current_site_theme_dir(self):
        """
        Tests current site theme name.
        """
        factory = RequestFactory()
        with mock.patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            current_site = get_current_site_theme_dir()
            self.assertEqual(current_site, 'red-theme')

    @with_comprehensive_theme('red-theme')
    @mock.patch('django.core.cache')
    def test_get_current_site_theme_dir_transaction_exception_scenario(self, mock_cache):
        """
        Confirm that the operation exits gracefully when encountering a TransactionManagementError
        """
        factory = RequestFactory()
        with mock.patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            # Set up the mocked response to get_current_site, which will throw a TransactionManagementError
            with mock.patch(
                'openedx.core.djangoapps.theming.helpers.get_current_site',
                return_value=mock.Mock(**{"themes.first.side_effect": TransactionManagementError}),
            ):
                mock_cache = mock.Mock()
                mock_cache.get.return_value = None

                # The TransactionManagementError should cause get_current_site_theme_dir to return "None"
                theme_dir = get_current_site_theme_dir()
                self.assertIsNone(theme_dir)
