"""
Django metadata for the Low Level Courses and Course Runs Django application.
"""
from django.apps import AppConfig


class CoursesConfig(AppConfig):
    """
    Configuration for the Courses Django application.
    """

    name = "openedx.core.djangoapps.content.courses"
    verbose_name = "Learning Core Course Prototype > Courses"
    default_auto_field = "django.db.models.BigAutoField"
    label = "oel_courses"
