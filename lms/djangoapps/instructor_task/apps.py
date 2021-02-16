"""
Instructor Task Application Configuration
"""

from django.apps import AppConfig


class InstructorTaskConfig(AppConfig):
    """
    Application Configuration for Instructor Task
    """
    name = 'lms.djangoapps.instructor_task'

    def ready(self):
        pass
