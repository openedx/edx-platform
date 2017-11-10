"""
Test background.py
"""

from django.test import TestCase
from django.dispatch import receiver

from edx_notifications.background import (
    perform_notification_scan,
    fire_background_notification_check,
)

_SIGNAL_RAISED = False


@receiver(perform_notification_scan)
def verify_signal_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Simple handler
    """
    global _SIGNAL_RAISED  # pylint: disable=global-statement
    _SIGNAL_RAISED = True


class BackgroundTests(TestCase):
    """
    Test cases for background.py
    """

    def setUp(self):
        global _SIGNAL_RAISED  # pylint: disable=global-statement
        _SIGNAL_RAISED = False

    def test_signal_raised(self):
        """
        Verifies that a signal has been raised
        """

        fire_background_notification_check()

        self.assertTrue(_SIGNAL_RAISED)
