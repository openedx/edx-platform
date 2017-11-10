"""
Notification types that will be used in common use cases for mobile apps notifications
"""

from django.dispatch import receiver

from edx_notifications.data import (
    NotificationType
)
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register some standard NotificationTypes.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_type_registrations' signal)
    """

    register_notification_type(
        NotificationType(
            name='open-edx.mobileapps.notifications',
            renderer='edx_notifications.renderers.basic.JsonRenderer'  # using this for tests to pass.
        )
    )
