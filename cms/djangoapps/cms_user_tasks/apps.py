"""
CMS user tasks application aonfiguration

Signal handlers are connected here.
"""

from django.apps import AppConfig


class CmsUserTasksConfig(AppConfig):
    """
    Application Configuration for cms_user_tasks.
    """
    name = u'cms_user_tasks'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import signals_user_tasks  # pylint: disable=unused-variable
