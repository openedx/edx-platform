"""
Remote Gradebook Application Configuration
"""

from django.apps import AppConfig
from openedx.core.constants import COURSE_ID_PATTERN
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class RemoteGradebookConfig(AppConfig):
    """
    Configuration class for Remote Gradebook Django app
    """
    name = u'lms.djangoapps.remote_gradebook'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: u'courses/{}/remote_gradebook/api/'.format(COURSE_ID_PATTERN),
                PluginURLs.RELATIVE_PATH: u'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: u'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
            }
        }
    }
