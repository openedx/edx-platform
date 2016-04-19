"""
Tests for comprehensive theme static files finders.
"""
import unittest

from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.theming.finders import ThemeFilesFinder


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestThemeFinders(TestCase):
    """
    Test comprehensive theming static files finders.
    """

    def setUp(self):
        super(TestThemeFinders, self).setUp()
        self.finder = ThemeFilesFinder()

    def test_find_first_themed_asset(self):
        """
        Verify Theme Finder returns themed assets
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]
        asset = "test-theme/images/logo.png"
        match = self.finder.find(asset)

        self.assertEqual(match, themes_dir / "test-theme" / "lms" / "static" / "images" / "logo.png")

    def test_find_all_themed_asset(self):
        """
        Verify Theme Finder returns themed assets
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]

        asset = "test-theme/images/logo.png"
        matches = self.finder.find(asset, all=True)

        # Make sure only first match was returned
        self.assertEqual(1, len(matches))

        self.assertEqual(matches[0], themes_dir / "test-theme" / "lms" / "static" / "images" / "logo.png")

    def test_find_in_theme(self):
        """
        Verify find in theme method of finders returns asset from specified theme
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]

        asset = "images/logo.png"
        match = self.finder.find_in_theme("test-theme", asset)

        self.assertEqual(match, themes_dir / "test-theme" / "lms" / "static" / "images" / "logo.png")
