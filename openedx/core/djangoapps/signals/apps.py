"""
Signal handlers are registered at startup here.
"""

from django.apps import AppConfig


class SignalConfig(AppConfig):
    """
    Application Configuration for Signals.
    """
    name = u'openedx.core.djangoapps.signals'

    def ready(self):
        """
        Connect handlers.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from . import signals, handlers  # pylint: disable=unused-variable
