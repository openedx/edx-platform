"""
Instructor Task Application Configuration
"""

from django.apps import AppConfig


class InstructorTaskConfig(AppConfig):
    """
    Application Configuration for Instructor Task
    """
    name = u'lms.djangoapps.instructor_task'


class InstructorTaskCeleryConfig(InstructorTaskConfig):
    """
    Celery-specific App config to force the loading of tasks.

    This will break tests if loaded as the normal AppConfig in INSTALLED_APPS
    outside of celery.
    """
    def ready(self):
        # noinspection PyUnresolvedReferences
        super().ready()
        from . import tasks  # pylint: disable=unused-import
