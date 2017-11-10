"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""

import pytz
from datetime import datetime, timedelta

from django.test import TestCase
from django.dispatch import receiver

from edx_notifications.management.commands import background_notification_check

from edx_notifications.stores.store import notification_store
from edx_notifications.background import (
    perform_notification_scan,
)
from edx_notifications.data import NotificationCallbackTimer


_SIGNAL_RAISED = False


@receiver(perform_notification_scan)
def verify_signal_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Simple handler
    """
    global _SIGNAL_RAISED  # pylint: disable=global-statement
    _SIGNAL_RAISED = True


class BackgroundCheckTest(TestCase):
    """
    Test suite for the management command
    """

    def test_background_check(self):
        """
        Invoke the Management Command
        """

        background_notification_check.Command().handle()

        self.assertTrue(_SIGNAL_RAISED)

    def test_timer_execution(self):
        """
        Make sure that Django management command runs through the timers
        """

        timer = NotificationCallbackTimer(
            name='foo',
            class_name='edx_notifications.tests.test_timer.NullNotificationCallbackTimerHandler',
            callback_at=datetime.now(pytz.UTC) - timedelta(days=1),
            context={},
            is_active=True,
        )

        notification_store().save_notification_timer(timer)

        background_notification_check.Command().handle()

        readback_timer = notification_store().get_notification_timer(timer.name)

        self.assertIsNotNone(readback_timer.executed_at)
        self.assertIsNone(readback_timer.err_msg)
