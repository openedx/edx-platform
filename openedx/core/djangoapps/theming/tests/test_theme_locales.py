"""
Tests for Theming locales
"""
import os

from django.conf import settings
from django.test import TestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestComprehensiveThemeLocale(TestCase):
    """
    Test Comprehensive Theme Locales
    """
    @skip_unless_lms
    def test_theme_locale_path_in_settings(self):
        """
        test comprehensive theming paths in settings.
        """
        self.assertIn(settings.REPO_ROOT / 'themes/conf/locale', settings.LOCALE_PATHS)  # pylint: disable=no-member

    def test_theme_locale_path_exist(self):
        """
        test comprehensive theming directory path exist.
        """
        self.assertTrue(os.path.exists(settings.REPO_ROOT / "themes/conf/locale"))
