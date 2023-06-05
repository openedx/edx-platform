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
    name = u'lms.djangoapps.instructor'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: u'^courses/{}/instructor/api/'.format(COURSE_ID_PATTERN),
                PluginURLs.RELATIVE_PATH: u'views.api_urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: u'settings.test'},
            }
        }
    }

    def ready(self):
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import InstructorService
            set_runtime_service('instructor', InstructorService())
