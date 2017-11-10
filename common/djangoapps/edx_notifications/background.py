"""
All code to support background Notification triggers
"""

from edx_notifications.signals import perform_notification_scan

# import edx_notifications.timer because it will register a signal receiver
# and if that Python module is not loaded, it will not be hooked up
import edx_notifications.timer  # pylint: disable=unused-import


def fire_background_notification_check():
    """
    This method will evoke the Django signal which applications can receive and perform any logic to see
    if any Notifications should be fired
    """

    perform_notification_scan.send(sender=None)
