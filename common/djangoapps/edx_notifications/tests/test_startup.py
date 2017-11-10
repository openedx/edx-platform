"""
Tests for the startup process
"""

from django.test import TestCase
from django.dispatch import receiver

from edx_notifications import startup

_SIGNAL_RAISED = False


@receiver(startup.perform_type_registrations)
def perform_type_registrations_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Simple handler
    """
    global _SIGNAL_RAISED  # pylint: disable=global-statement
    _SIGNAL_RAISED = True


class StartupTests(TestCase):
    """
    Test cases for startup.py
    """

    def setUp(self):
        global _SIGNAL_RAISED  # pylint: disable=global-statement
        _SIGNAL_RAISED = False

    def test_signal_raised(self):
        """
        Verifies that a signal has been raised
        """

        startup.initialize()

        self.assertTrue(_SIGNAL_RAISED)
