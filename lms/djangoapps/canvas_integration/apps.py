"""
Remote Gradebook Application Configuration
"""

from django.apps import AppConfig
from openedx.core.constants import COURSE_ID_PATTERN
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class CanvasIntegrationConfig(AppConfig):
    """
    Configuration class for Canvas integration app
    """
    name = u'canvas_integration'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                # TODO
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: u'courses/{}/canvas/api/'.format(COURSE_ID_PATTERN),
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
