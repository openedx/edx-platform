"""
Django Application Configuration for course_structures app.
"""
from django.apps import AppConfig


class CourseStructuresConfig(AppConfig):
    """
    Custom AppConfig for openedx.core.djangoapps.content.course_structures
    """
    name = u'openedx.core.djangoapps.content.course_structures'

    def ready(self):
        """
        Define tasks to perform at app loading time:

        * Connect signal handlers
        """
        from . import signals  # pylint: disable=unused-variable
