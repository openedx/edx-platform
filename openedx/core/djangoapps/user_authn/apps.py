"""
User Authentication Configuration
"""

from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class UserAuthnConfig(AppConfig):
    """
    Application Configuration for User Authentication.
    """
    name = 'openedx.core.djangoapps.user_authn'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: '',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
        },
    }
