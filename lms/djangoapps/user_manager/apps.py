"""
User Manager Application Configuration
"""

from django.apps import AppConfig


class UserManagerConfig(AppConfig):
    """
    Application Configuration for user_manager.
    """
    name = 'lms.djangoapps.user_manager'
    verbose_name = 'User Manager Application'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import signals  # pylint: disable=unused-variable
