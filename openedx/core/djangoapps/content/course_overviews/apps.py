"""
Configuration for course_overviews Django app
"""


from django.apps import AppConfig


class CourseOverviewsConfig(AppConfig):
    """
    Configuration class for course_overviews Django app
    """
    name = 'openedx.core.djangoapps.content.course_overviews'
    verbose_name = "Course Overviews"

    def ready(self):
        pass
