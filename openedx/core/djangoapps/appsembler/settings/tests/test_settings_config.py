"""Tests the SettingsConfig class

"""
from django.apps.registry import apps

from openedx.core.djangoapps.appsembler.settings.apps import SettingsConfig


def test_config():
    """
    Basic test to check that the app loads
    """
    app_name = 'openedx.core.djangoapps.appsembler.settings'
    assert SettingsConfig.name == app_name
    assert hasattr(SettingsConfig, 'plugin_app')
    assert apps.is_installed(app_name)
    app_config = apps.get_containing_app_config(app_name)
    assert app_config
