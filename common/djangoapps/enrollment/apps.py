"""
Enrollment Application Configuration

Signal handlers are connected here.
"""

from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    """
    Application configuration for enrollments.
    """
    name = u'enrollment'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import handlers  # pylint: disable=unused-variable
