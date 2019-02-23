"""
Configuration for bookmarks Django app
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class BookmarksConfig(AppConfig):
    """
    Configuration class for bookmarks Django app
    """
    name = 'openedx.core.djangoapps.bookmarks'
    verbose_name = _("Bookmarks")

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: 'api/bookmarks/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: 'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
            }
        }
    }

    def ready(self):
        # Register the signals handled by bookmarks.
        from . import signals
