"""
Configure the django app
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginSettings
from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class DiscussionsConfig(AppConfig):
    """
    Configure the discussions django app
    """
    name = 'openedx.core.djangoapps.discussions'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: r'^discussions/',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
        },
        PluginSettings.CONFIG: {
        },
    }
