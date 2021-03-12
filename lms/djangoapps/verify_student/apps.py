"""
Student Identity Verification Application Configuration
"""


from django.apps import AppConfig


class VerifyStudentConfig(AppConfig):
    """
    Application Configuration for verify_student.
    """
    name = 'lms.djangoapps.verify_student'
    verbose_name = 'Student Identity Verification'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import signals  # pylint: disable=unused-import
        from . import tasks    # pylint: disable=unused-import
