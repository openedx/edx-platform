"""
Grades Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig
from django.conf import settings
from edx_django_utils.plugins import PluginSettings, PluginURLs
from edx_proctoring.runtime import set_runtime_service

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class GradesConfig(AppConfig):
    """
    Application Configuration for Grades.
    """
    name = u'lms.djangoapps.grades'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'grades_api',
                PluginURLs.REGEX: u'^api/grades/',
                PluginURLs.RELATIVE_PATH: u'rest_api.urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: u'settings.test'},
            }
        }
    }

    def ready(self):
        """
        Connect handlers to recalculate grades.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from .signals import handlers  # pylint: disable=unused-import
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import GradesService
            set_runtime_service('grades', GradesService())
