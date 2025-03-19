"""
Announcements Application Configuration
"""


from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs, PluginSettings

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class AnnouncementsConfig(AppConfig):
    """
    Application Configuration for Announcements
    """
    name = 'openedx.features.announcements'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'announcements',
                PluginURLs.REGEX: '^announcements/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: 'settings.test'},
            }
        }
    }
