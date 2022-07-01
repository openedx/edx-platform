"""
Define the funix_relative_date Django App.
"""
from django.apps import AppConfig

class FunixRelativeDateConfig(AppConfig):
    """
    Application Configuration for FunixRelativeDate.
    """
    name = 'openedx.features.funix_relative_date'
    def ready(self):
        """
        Connect signal handlers.
        """
        from . import handlers  # pylint: disable=unused-import
