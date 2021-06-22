"""
All configurations for webinars app
"""
from django.apps import AppConfig


class WebinarsConfig(AppConfig):
    """
    Webinars app configuration.
    """

    name = 'openedx.adg.lms.webinars'

    def ready(self):
        """
        This method is called as soon as the registry is fully populated and is used to perform initialization task.
        Overriding this method to register signals.
        """
        from . import handlers  # pylint: disable=unused-import
