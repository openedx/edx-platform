"""Tests for the Studio tab plugin API."""
from django.test import TestCase
import mock

from cms.lib.studio_tabs import StudioTabPluginManager
from openedx.core.lib.api.plugins import PluginError


class TestStudioTabPluginApi(TestCase):
    """Unit tests for the Studio tab plugin API."""

    @mock.patch('cms.lib.studio_tabs.StudioTabPluginManager.get_available_plugins')
    def test_get_enabled_tabs(self, get_available_plugins):
        """Verify that only enabled tabs are retrieved."""
        enabled_tab = self._mock_tab(is_enabled=True)
        mock_tabs = {
            'disabled_tab': self._mock_tab(),
            'enabled_tab': enabled_tab,
        }

        get_available_plugins.return_value = mock_tabs

        self.assertEqual(StudioTabPluginManager.get_enabled_tabs(), [enabled_tab])

    def test_get_invalid_plugin(self):
        """Verify that get_plugin fails when an invalid plugin is requested."""
        with self.assertRaises(PluginError):
            StudioTabPluginManager.get_plugin('invalid_tab')

    def _mock_tab(self, is_enabled=False):
        """Generate a mock tab."""
        tab = mock.Mock()
        tab.is_enabled = mock.Mock(return_value=is_enabled)

        return tab
