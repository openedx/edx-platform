"""
Test cms startup
"""

from django.conf import settings

from django.test import TestCase
from django.test.utils import override_settings

from mock import patch
from cms.startup import run, enable_theme


class StartupTestCase(TestCase):
    """
    Test cms startup
    """

    def setUp(self):
        super(StartupTestCase, self).setUp()

    @patch.dict("django.conf.settings.FEATURES", {"USE_CUSTOM_THEME": True})
    @override_settings(THEME_NAME="bar")
    def test_run_with_theme(self):
        self.assertEqual(settings.FEATURES["USE_CUSTOM_THEME"], True)
        with patch('cms.startup.enable_theme') as mock_enable_theme:
            run()
            self.assertTrue(mock_enable_theme.called)

    @patch.dict("django.conf.settings.FEATURES", {"USE_CUSTOM_THEME": False})
    def test_run_without_theme(self):
        self.assertEqual(settings.FEATURES["USE_CUSTOM_THEME"], False)
        with patch('cms.startup.enable_theme') as mock_enable_theme:
            run()
            self.assertFalse(mock_enable_theme.called)

    @patch.dict("django.conf.settings.FEATURES", {"USE_CUSTOM_THEME": True})
    @override_settings(THEME_NAME="bar")
    @override_settings(FAVICON_PATH="images/favicon.ico")
    def test_enable_theme(self):
        enable_theme()
        self.assertEqual(
            settings.FAVICON_PATH,
            'themes/bar/images/favicon.ico'
        )
        exp_path = (u'themes/bar', settings.ENV_ROOT / "themes/bar/static")
        self.assertIn(exp_path, settings.STATICFILES_DIRS)
