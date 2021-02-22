"""
Basic Configuration for Nodebb app
"""
from django.apps import AppConfig


class NodebbConfig(AppConfig):
    name = u'nodebb'

    def ready(self):
        """
        Connect signal handlers.
        """
        import nodebb.signals.handlers  # pylint: disable=unused-variable
