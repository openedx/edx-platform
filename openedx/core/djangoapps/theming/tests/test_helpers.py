"""
Test helpers for Comprehensive Theming.
"""
import unittest
from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming import helpers as theming_helpers
from openedx.core.djangoapps.theming.helpers import get_template_path_with_theme, strip_site_theme_templates_path, \
    get_themes, Theme, get_theme_base_dir


class TestHelpers(TestCase):
    """Test comprehensive theming helper functions."""

    def test_get_themes(self):
        """
        Tests template paths are returned from enabled theme.
        """
        expected_themes = [
            Theme('test-theme', 'test-theme', get_theme_base_dir('test-theme')),
            Theme('red-theme', 'red-theme', get_theme_base_dir('red-theme')),
            Theme('edge.edx.org', 'edge.edx.org', get_theme_base_dir('edge.edx.org')),
            Theme('edx.org', 'edx.org', get_theme_base_dir('edx.org')),
            Theme('example', 'example', get_theme_base_dir('example')),
            Theme('stanford-style', 'stanford-style', get_theme_base_dir('stanford-style')),
        ]
        actual_themes = get_themes()
        self.assertItemsEqual(expected_themes, actual_themes)

    @override_settings(COMPREHENSIVE_THEME_DIRS=[settings.TEST_THEME.dirname()])
    def test_get_themes_2(self):
        """
        Tests template paths are returned from enabled theme.
        """
        expected_themes = [
            Theme('test-theme', 'test-theme', get_theme_base_dir('test-theme')),
        ]
        actual_themes = get_themes()
        self.assertItemsEqual(expected_themes, actual_themes)

    def test_get_value_returns_override(self):
        """
        Tests to make sure the get_value() operation returns a combined dictionary consisting
        of the base container with overridden keys from the site configuration
        """
        with patch('openedx.core.djangoapps.site_configuration.helpers.get_value') as mock_get_value:
            override_key = 'JWT_ISSUER'
            override_value = 'testing'
            mock_get_value.return_value = {override_key: override_value}
            jwt_auth = configuration_helpers.get_value('JWT_AUTH')
            self.assertEqual(jwt_auth[override_key], override_value)

    def test_is_comprehensive_theming_enabled(self):
        """
        Tests to make sure the is_comprehensive_theming_enabled function works as expected.
        Here are different scenarios that we need to test

        1. Theming is enabled, there is a SiteTheme record and microsite configuration for the current site.
            is_comprehensive_theming_enabled should return True
        2. Theming is enabled, there is no SiteTheme record but there is microsite configuration for the current site.
            is_comprehensive_theming_enabled should return False
        3. Theming is enabled, there is neither a SiteTheme record nor microsite configuration for the current site.
            is_comprehensive_theming_enabled should return True
        4. Theming is disabled, there is a SiteTheme record and microsite configuration for the current site.
            is_comprehensive_theming_enabled should return False
        5. Theming is disabled, there is no SiteTheme record but there is microsite configuration for the current site.
            is_comprehensive_theming_enabled should return False
        6. Theming is disabled, there is neither a SiteTheme record nor microsite configuration for the current site.
            is_comprehensive_theming_enabled should return False
        """
        # Theming is enabled, there is a SiteTheme record and microsite configuration for the current site
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=True),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                self.assertTrue(theming_helpers.is_comprehensive_theming_enabled())

        # Theming is enabled, there is no SiteTheme record but there is microsite configuration for the current site.
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=False),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                self.assertFalse(theming_helpers.is_comprehensive_theming_enabled())

        # Theming is enabled, there is neither a SiteTheme record nor microsite configuration for the current site.
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=False),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=False),
            ):
                self.assertTrue(theming_helpers.is_comprehensive_theming_enabled())

        with override_settings(ENABLE_COMPREHENSIVE_THEMING=False):
            # Theming is disabled, there is a SiteTheme record and microsite configuration for the current site.
            with patch(
                "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
                Mock(return_value=True),
            ):
                with patch(
                    "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                    Mock(return_value=True),
                ):
                    self.assertFalse(theming_helpers.is_comprehensive_theming_enabled())

            # Theming is disabled, there is no SiteTheme record but
            # there is microsite configuration for the current site.
            with patch(
                "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
                Mock(return_value=False),
            ):
                with patch(
                    "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                    Mock(return_value=True),
                ):
                    self.assertFalse(theming_helpers.is_comprehensive_theming_enabled())

            # Theming is disabled, there is neither a SiteTheme record nor microsite configuration for the current site.
            with patch(
                "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
                Mock(return_value=False),
            ):
                with patch(
                    "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                    Mock(return_value=False),
                ):
                    self.assertFalse(theming_helpers.is_comprehensive_theming_enabled())

    def test_get_template(self):
        """
        Tests to make sure the get_template function works as expected.
        """
        # if the current site has associated SiteTheme then get_template should return None
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=True),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                with patch("microsite_configuration.microsite.TEMPLATES_BACKEND") as mock_microsite_backend:
                    mock_microsite_backend.get_template = Mock(return_value="/microsite/about.html")
                    self.assertIsNone(theming_helpers.get_template("about.html"))

        # if the current site does not have associated SiteTheme then get_template should return microsite override
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=False),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                with patch("microsite_configuration.microsite.TEMPLATES_BACKEND") as mock_microsite_backend:
                    mock_microsite_backend.get_template = Mock(return_value="/microsite/about.html")
                    self.assertEqual(theming_helpers.get_template("about.html"), "/microsite/about.html")

    def test_get_template_path(self):
        """
        Tests to make sure the get_template_path function works as expected.
        """
        # if the current site has associated SiteTheme then get_template_path should return the argument as is.
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=True),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                with patch("microsite_configuration.microsite.TEMPLATES_BACKEND") as mock_microsite_backend:
                    mock_microsite_backend.get_template = Mock(return_value="/microsite/about.html")
                    self.assertEqual(theming_helpers.get_template_path("about.html"), "about.html")

        # if the current site does not have associated SiteTheme then get_template_path should return microsite override
        with patch(
            "openedx.core.djangoapps.theming.helpers.current_request_has_associated_site_theme",
            Mock(return_value=False),
        ):
            with patch(
                "openedx.core.djangoapps.theming.helpers.microsite.is_request_in_microsite",
                Mock(return_value=True),
            ):
                with patch("microsite_configuration.microsite.TEMPLATES_BACKEND") as mock_microsite_backend:
                    mock_microsite_backend.get_template_path = Mock(return_value="/microsite/about.html")
                    self.assertEqual(theming_helpers.get_template_path("about.html"), "/microsite/about.html")


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestHelpersLMS(TestCase):
    """Test comprehensive theming helper functions."""

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('header.html')
        self.assertEqual(template_path, 'red-theme/lms/templates/header.html')

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


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestHelpersCMS(TestCase):
    """Test comprehensive theming helper functions."""

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('login.html')
        self.assertEqual(template_path, 'red-theme/cms/templates/login.html')

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
