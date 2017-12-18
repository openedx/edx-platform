"""
Discussion Application Configuration

Signal handlers are connected here.
"""

from django.apps import AppConfig


class DiscussionConfig(AppConfig):
    """
    Application Configuration for Grades.
    """
    name = u'lms.djangoapps.discussion'

    def ready(self):
        """
        Connect handlers to send notifications about discussions.
        """
        from .signals import handlers  # pylint: disable=unused-variable
