"""
Instructor Application Configuration
"""

from django.apps import AppConfig
from django.conf import settings
from edx_proctoring.runtime import set_runtime_service


class InstructorConfig(AppConfig):
    """
    Default configuration for the "lms.djangoapps.instructor" Django application.
    """
    name = u'lms.djangoapps.instructor'

    def ready(self):
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import InstructorService
            set_runtime_service('instructor', InstructorService())
