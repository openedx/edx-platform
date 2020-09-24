"""
Badges Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig


class BadgesConfig(AppConfig):
    """
    Application Configuration for Badges.
    """
    name = u'lms.djangoapps.badges'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import handlers  # pylint: disable=unused-import
