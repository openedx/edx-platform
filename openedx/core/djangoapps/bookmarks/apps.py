"""
Configuration for bookmarks Django app
"""


from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from edx_django_utils.plugins import PluginSettings, PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class BookmarksConfig(AppConfig):
    """
    Configuration class for bookmarks Django app
    """
    name = 'openedx.core.djangoapps.bookmarks'
    verbose_name = _("Bookmarks")

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: u'^api/bookmarks/',
                PluginURLs.RELATIVE_PATH: u'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
            }
        }
    }

    def ready(self):
        # Register the signals handled by bookmarks.
        from . import signals
