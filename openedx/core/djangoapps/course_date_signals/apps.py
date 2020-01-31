"""
Django app configuration for openedx.core.djangoapps.course_dates_signals
"""

from django.apps import AppConfig


class CourseDatesSignalsConfig(AppConfig):
    name = 'openedx.core.djangoapps.course_dates_signals'

    def ready(self):
        """
        Connect handlers to signals.
        """
        from . import handlers  # pylint: disable=unused-variable
