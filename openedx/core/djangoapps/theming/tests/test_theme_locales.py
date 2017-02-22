"""
Tests for Themeing locales
"""

import unittest
from django.conf import settings
from django.test import TestCase
import os


class TestComprehensiveThemeLocale(TestCase):
    """
    Test Comprehensive Theme Locales
    """
    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
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
