"""
Configuration for the ``student`` Django application.
"""


import os

from django.apps import AppConfig


class StudentConfig(AppConfig):
    """
    Default configuration for the ``student`` application.
    """
    name = 'student'

    def ready(self):
        # Connect signal handlers.
        from .signals import receivers  # pylint: disable=unused-import

        # The django-simple-history model on CourseEnrollment creates performance
        # problems in testing, we mock it here so that the mock impacts all tests.
        if os.environ.get('DISABLE_COURSEENROLLMENT_HISTORY', False):
            import student.models as student_models
            from mock import MagicMock

            student_models.CourseEnrollment.history = MagicMock()
