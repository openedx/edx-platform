"""
Tests for Management commands of comprehensive theming.
"""

from django.core.management import call_command
from django.test import TestCase, override_settings
from unittest.mock import patch

import pavelib.assets


class TestUpdateAssets(TestCase):
    """
    Test comprehensive theming helper functions.
    """

    @patch.object(pavelib.assets, 'sh')
    @override_settings(COMPREHENSIVE_THEME_DIRS='common/test')
    def test_deprecated_wrapper(self, mock_sh):
        call_command('compile_sass', '--themes', 'fake-theme1', 'fake-theme2')
        assert mock_sh.called_once_with(
            "npm run compile-sass -- " +
            "--theme-dir common/test --theme fake-theme-1 --theme fake-theme-2"
        )
