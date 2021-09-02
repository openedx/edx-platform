"""
Dashboard App Config
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginSettings, PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class AdminDashboardConfig(AppConfig):
    name = 'openedx.features.wikimedia_features.admin_dashboard'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'admin_dashboard',
                PluginURLs.REGEX: '^admin_dashboard/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
            }
        }
    }
