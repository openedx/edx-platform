"""
Configuration for bookmarks Django app
"""
from django.apps import AppConfig


class BookmarksConfig(AppConfig):
    """
    Configuration class for bookmarks Django app
    """
    name = 'openedx.core.djangoapps.bookmarks'
    verbose_name = "Bookmarks"

    def ready(self):
        # Register the signals handled by bookmarks.
        from . import signals
