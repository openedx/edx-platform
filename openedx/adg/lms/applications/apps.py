"""
All configurations for applications app
"""
from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    """
    Applications app configuration.
    """
    name = 'openedx.adg.lms.applications'

    def ready(self):
        from . import handlers  # pylint: disable=unused-import
