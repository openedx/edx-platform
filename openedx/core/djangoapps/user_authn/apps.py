"""
User Authentication Configuration
"""


from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import PluginURLs, ProjectType


class UserAuthnConfig(AppConfig):
    """
    Application Configuration for User Authentication.
    """
    name = u'openedx.core.djangoapps.user_authn'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: u'',
                PluginURLs.RELATIVE_PATH: u'urls',
            },
        },
    }
