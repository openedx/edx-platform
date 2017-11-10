"""
Django signals that can be raised by the Notification subsystem
"""

from django.dispatch import Signal


# Signal to all receivers that they should go register their NotificationTypes into
# the subsystem
perform_type_registrations = Signal(providing_args=[])  # pylint: disable=invalid-name

# Signal to all receivers that they should go register their NotificationTimers/Callbacks into
# the subsystem
perform_timer_registrations = Signal(providing_args=[])  # pylint: disable=invalid-name

# Signal to all receivers that they should go through and perform any checks
# as to conditions when
perform_notification_scan = Signal(providing_args=[])  # pylint: disable=invalid-name
