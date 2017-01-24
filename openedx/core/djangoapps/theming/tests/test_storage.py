"""
Tests for comprehensive theme static files storage classes.
"""
import ddt
import re

from mock import patch

from django.test import TestCase, override_settings
from django.conf import settings

from openedx.core.djangoapps.theming.helpers import get_theme_base_dirs, Theme, get_theme_base_dir
from openedx.core.djangoapps.theming.storage import ThemeStorage
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
@ddt.ddt
class TestStorageLMS(TestCase):
    """
    Test comprehensive theming static files storage.
    """

    def setUp(self):
        super(TestStorageLMS, self).setUp()
        self.themes_dir = get_theme_base_dirs()[0]
        self.enabled_theme = "red-theme"
        self.system_dir = settings.REPO_ROOT / "lms"
        self.storage = ThemeStorage(location=self.themes_dir / self.enabled_theme / 'lms' / 'static')

    @override_settings(DEBUG=True)
    @ddt.data(
        (True, "images/logo.png"),
        (True, "images/favicon.ico"),
        (False, "images/spinning.gif"),
    )
    @ddt.unpack
    def test_themed(self, is_themed, asset):
        """
        Verify storage returns True on themed assets
        """
        self.assertEqual(is_themed, self.storage.themed(asset, self.enabled_theme))

    @override_settings(DEBUG=True)
    @ddt.data(
        ("images/logo.png", ),
        ("images/favicon.ico", ),
    )
    @ddt.unpack
    def test_url(self, asset):
        """
        Verify storage returns correct url depending upon the enabled theme
        """
        with patch(
            "openedx.core.djangoapps.theming.storage.get_current_theme",
            return_value=Theme(self.enabled_theme, self.enabled_theme, get_theme_base_dir(self.enabled_theme)),
        ):
            asset_url = self.storage.url(asset)
            # remove hash key from file url
            asset_url = re.sub(r"(\.\w+)(\.png|\.ico)$", r"\g<2>", asset_url)
            expected_url = self.storage.base_url + self.enabled_theme + "/" + asset

            self.assertEqual(asset_url, expected_url)

    @override_settings(DEBUG=True)
    @ddt.data(
        ("images/logo.png", ),
        ("images/favicon.ico", ),
    )
    @ddt.unpack
    def test_path(self, asset):
        """
        Verify storage returns correct file path depending upon the enabled theme
        """
        with patch(
            "openedx.core.djangoapps.theming.storage.get_current_theme",
            return_value=Theme(self.enabled_theme, self.enabled_theme, get_theme_base_dir(self.enabled_theme)),
        ):
            returned_path = self.storage.path(asset)
            expected_path = self.themes_dir / self.enabled_theme / "lms/static/" / asset

            self.assertEqual(expected_path, returned_path)
