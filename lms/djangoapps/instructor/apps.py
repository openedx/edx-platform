"""
Instructor Application Configuration
"""


from django.apps import AppConfig
from django.conf import settings
from edx_django_utils.plugins import PluginSettings, PluginURLs
from edx_proctoring.runtime import set_runtime_service

from openedx.core.constants import COURSE_ID_PATTERN
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class InstructorConfig(AppConfig):
    """
    Application Configuration for Instructor.
    """
    name = 'lms.djangoapps.instructor'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: f'^courses/{COURSE_ID_PATTERN}/instructor/api/',
                PluginURLs.RELATIVE_PATH: 'views.api_urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: 'settings.devstack'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: 'settings.test'},
            }
        }
    }

    def ready(self):
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import InstructorService
            set_runtime_service('instructor', InstructorService())
