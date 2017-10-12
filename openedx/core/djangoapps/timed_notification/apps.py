from django.apps import AppConfig


class TimedNotificationConfig(AppConfig):
    name = u'openedx.core.djangoapps.timed_notification'

    def ready(self):
        """
        Connect notification signals.
        """
        from . import notifications
