"""
Configure the django app
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginSettings
from edx_django_utils.plugins import PluginURLs


class DiscussionsConfig(AppConfig):
    """
    Configure the discussions django app
    """
    name = 'openedx.core.djangoapps.discussions'
    plugin_app = {
        PluginURLs.CONFIG: {
        },
        PluginSettings.CONFIG: {
        },
    }
