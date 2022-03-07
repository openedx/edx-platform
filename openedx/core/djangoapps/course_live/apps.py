"""
Configure the django app
"""
from django.apps import AppConfig


class CourseLiveConfig(AppConfig):
    """
    Configuration class for Course Live.
    """

    name = "openedx.core.djangoapps.course_live"

    plugin_app = {}
