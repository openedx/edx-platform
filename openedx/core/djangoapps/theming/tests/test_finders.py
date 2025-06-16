"""
Tests for comprehensive theme static files finders.
"""


from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.theming.finders import ThemeFilesFinder
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class TestThemeFinders(TestCase):
    """
    Test comprehensive theming static files finders.
    """

    def setUp(self):
        super().setUp()
        self.finder = ThemeFilesFinder()

    def test_find_first_themed_asset(self):
        """
        Verify Theme Finder returns themed assets
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]
        asset = "test-theme/images/logo.png"
        match = self.finder.find(asset)

        assert match == (((((themes_dir / 'test-theme') / 'lms') / 'static') / 'images') / 'logo.png')

    def test_find_all_themed_asset(self):
        """
        Verify Theme Finder returns themed assets
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]

        asset = "test-theme/images/logo.png"
        matches_test_1 = self.finder.find(asset, True)
        matches_test_2 = self.finder.find(asset, all=True)
        matches_test_3 = self.finder.find(asset, find_all=True)

        #1 Make sure only first match was returned
        assert 1 == len(matches_test_1)
        assert matches_test_1[0] == (((((themes_dir / 'test-theme') / 'lms') / 'static') / 'images') / 'logo.png')

        #2 Make sure only first match was returned
        assert 1 == len(matches_test_2)
        assert matches_test_2[0] == (((((themes_dir / 'test-theme') / 'lms') / 'static') / 'images') / 'logo.png')

        #3 Make sure only first match was returned
        assert 1 == len(matches_test_3)
        assert matches_test_3[0] == (((((themes_dir / 'test-theme') / 'lms') / 'static') / 'images') / 'logo.png')

    def test_find_in_theme(self):
        """
        Verify find in theme method of finders returns asset from specified theme
        """
        themes_dir = settings.COMPREHENSIVE_THEME_DIRS[1]

        asset = "images/logo.png"
        match = self.finder.find_in_theme("test-theme", asset)

        assert match == (((((themes_dir / 'test-theme') / 'lms') / 'static') / 'images') / 'logo.png')
