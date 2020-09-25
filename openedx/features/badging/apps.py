"""
Badging app configurations
"""
from django.apps import AppConfig


class BadgingConfig(AppConfig):
    name = u'openedx.features.badging'

    def ready(self):
        """
        Connect signal handlers.
        """
        import openedx.features.badging.handlers  # pylint: disable=unused-variable
