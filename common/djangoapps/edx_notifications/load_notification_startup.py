"""
One time initialization of the Notification subsystem
"""

from django.dispatch import receiver

from common.djangoapps.edx_notifications.lib.publisher import (
    register_notification_type,
)

from common.djangoapps.edx_notifications.data import (
    NotificationType,
)

from edx_notifications import startup


@receiver(startup.perform_type_registrations)
def perform_type_registrations_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register test notification types
    """

    register_notification_type(
        NotificationType(
            name='philu.nodebb.user_mentioned_you_in',
            renderer='edx_notifications.renderers.basic.JsonRenderer',
        )
    )


def start_up():
    """
    Initialize the Notification subsystem
    """

    startup.initialize()
