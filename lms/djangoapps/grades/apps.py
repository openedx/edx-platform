"""
Grades Application Configuration

Signal handlers are connected here.
"""

from django.apps import AppConfig
from django.conf import settings
from edx_proctoring.runtime import set_runtime_service
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class GradesConfig(AppConfig):
    """
    Application Configuration for Grades.
    """
    name = 'lms.djangoapps.grades'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'grades_api',
                PluginURLs.REGEX: 'api/grades/',
                PluginURLs.RELATIVE_PATH: 'api.urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: 'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: 'settings.test'},
            }
        }
    }

    def ready(self):
        """
        Connect handlers to recalculate grades.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from .signals import handlers  # pylint: disable=unused-variable
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import GradesService
            set_runtime_service('grades', GradesService())
