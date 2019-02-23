"""
Journals Application Configuration
"""
from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class JournalsConfig(AppConfig):
    """
    Application Configuration for Journals.
    """
    name = 'openedx.features.journals'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: r'^journals/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: 'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: 'settings.devstack'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: 'settings.test'},
            }
        }
    }
