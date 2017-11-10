"""
Tests for the timer.py
"""

from freezegun import freeze_time
import pytz
from datetime import datetime, timedelta
from django.test import TestCase
from edx_notifications.management.commands import background_notification_check

from edx_notifications.stores.store import notification_store
from edx_notifications.callbacks import NotificationCallbackTimerHandler
from edx_notifications import startup
from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
    NotificationCallbackTimer
)
from edx_notifications.tests.test_scopes import TestListScopeResolver
from edx_notifications.scopes import register_user_scope_resolver
from edx_notifications.lib.publisher import publish_timed_notification, cancel_timed_notification
from edx_notifications.timer import poll_and_execute_timers
from edx_notifications.exceptions import ItemNotFoundError


class BadNotificationCallbackTimerHandler(NotificationCallbackTimerHandler):
    """
    Does bad things!
    """

    def notification_timer_callback(self, timer):
        """
        Does nothing
        """
        super(BadNotificationCallbackTimerHandler, self).notification_timer_callback(timer)


class NullNotificationCallbackTimerHandler(NotificationCallbackTimerHandler):
    """
    Does nothing
    """

    def notification_timer_callback(self, timer):
        """
        do nothing
        """
        return {}


class ExceptionNotificationCallbackTimerHandler(NotificationCallbackTimerHandler):
    """
    Raises an exception when called
    """

    def notification_timer_callback(self, timer):
        """
        Raise exception
        """
        raise Exception('This did not work!')


class TimerTests(TestCase):
    """
    Test cases for timer.py
    """

    def setUp(self):
        """
        Test setup
        """
        self.store = notification_store()

    def test_cant_instantiate_base(self):
        """
        Asserts that we cannot create an instance of NotificationCallbackTimerHandler
        """

        with self.assertRaises(TypeError):
            NotificationCallbackTimerHandler()

    def test_must_implement_method(self):
        """
        Asserts that a derived class of NotificationCallbackTimerHandler shouldn't
        call into the base class
        """

        with self.assertRaises(NotImplementedError):
            BadNotificationCallbackTimerHandler().notification_timer_callback(None)

    def test_recurring_timer(self):
        """
        Make sure recurring timers work
        """

        timer = NotificationCallbackTimer(
            name='foo',
            class_name='edx_notifications.tests.test_timer.NullNotificationCallbackTimerHandler',
            callback_at=datetime.now(pytz.UTC) - timedelta(days=1),
            context={},
            is_active=True,
            periodicity_min=1
        )

        self.store.save_notification_timer(timer)

        poll_and_execute_timers()

        timer1 = self.store.get_notification_timer(timer.name)
        self.assertIsNone(timer1.executed_at)  # should be marked as still to execute
        self.assertIsNone(timer1.err_msg)
        self.assertNotEqual(timer.callback_at, timer1.callback_at)  # verify the callback time is incremented

    def test_bad_handler(self):
        """
        Make sure that a timer with a bad class_name doesn't operate
        """

        timer = NotificationCallbackTimer(
            name='foo',
            class_name='edx_notifications.badmodule.BadHandler',
            callback_at=datetime.now(pytz.UTC) - timedelta(days=1),
            context={},
            is_active=True
        )

        self.store.save_notification_timer(timer)

        poll_and_execute_timers()

        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNotNone(updated_timer.err_msg)

    def test_error_in_execution(self):
        """
        Make sure recurring timers work
        """

        timer = NotificationCallbackTimer(
            name='foo',
            class_name='edx_notifications.tests.test_timer.ExceptionNotificationCallbackTimerHandler',
            callback_at=datetime.now(pytz.UTC) - timedelta(days=1),
            context={},
            is_active=True
        )

        self.store.save_notification_timer(timer)

        poll_and_execute_timers()

        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNotNone(updated_timer.err_msg)


class TimedNotificationsTests(TestCase):
    """
    Tests the creating of timed notifications
    """

    def setUp(self):
        """
        start up stuff
        """

        register_user_scope_resolver('list_scope', TestListScopeResolver())

        self.store = notification_store()
        self.msg_type = self.store.save_notification_type(
            NotificationType(
                name='foo.bar',
                renderer='foo',
            )
        )

        msg = NotificationMessage(
            msg_type=self.msg_type,
            payload={'foo': 'bar'},
        )
        msg.add_payload(
            {
                'extra': 'stuff'
            },
            channel_name='other_channel'
        )
        self.msg = self.store.save_notification_message(msg)

    def test_timed_notifications(self):
        """
        Tests that we can create a timed notification and make sure it gets
        executed with the timer polling
        """

        # assert we start have with no notifications
        self.assertEquals(self.store.get_num_notifications_for_user(1), 0)

        # set up a timer that is due in the past
        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(seconds=1),
            scope_name='user',
            scope_context={'user_id': 1}
        )

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNone(updated_timer.err_msg)
        self.assertIsNotNone(updated_timer.results)

        # assert we now have a notification due to the timer executing
        self.assertEquals(self.store.get_num_notifications_for_user(1), 1)

        notifications = self.store.get_notifications_for_user(1)
        self.assertEqual(len(notifications), 1)

        read_user_msg = notifications[0]
        self.assertEqual(read_user_msg.msg.payload, self.msg.get_payload())
        self.assertNotIn('extra', read_user_msg.msg.payload)

    def test_bad_scope(self):
        """
        Make sure we can't register a timer on a user scope that
        does not exist
        """

        with self.assertRaises(ValueError):
            publish_timed_notification(
                msg=self.msg,
                send_at=datetime.now(pytz.UTC) - timedelta(seconds=1),
                scope_name='bad-scope',
                scope_context={'user_id': 1}
            )

    def test_erred_timed_notifications(self):
        """
        Tests that we can create a timed notification and make sure it gets
        executed with the timer polling
        """

        # assert we start have with no notifications
        self.assertEquals(self.store.get_num_notifications_for_user(1), 0)

        # set up a timer that is due in the past
        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(seconds=1),
            scope_name='user',
            scope_context={}  # missing user_id
        )

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNotNone(updated_timer.err_msg)
        self.assertIsNotNone(updated_timer.results)
        self.assertIsNotNone(updated_timer.results['errors'])

        # should be no notifications
        self.assertEquals(self.store.get_num_notifications_for_user(1), 0)

    def test_timed_broadcast(self):
        """
        Tests that we can create a timed notification and make sure it gets
        executed with the timer polling
        """

        # set up a timer that is due in the past
        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(seconds=1),
            scope_name='list_scope',
            scope_context={'range': 5}
        )

        # assert we start have with no notifications
        for user_id in range(timer.context['distribution_scope']['scope_context']['range']):
            self.assertEquals(self.store.get_num_notifications_for_user(user_id), 0)

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNone(updated_timer.err_msg)

        # assert we now have a notification
        for user_id in range(timer.context['distribution_scope']['scope_context']['range']):
            self.assertEquals(self.store.get_num_notifications_for_user(user_id), 1)

    def test_wait_for_correct_time(self):
        """
        Make sure timers don't fire too early and they can be rescheduled
        """

        # set up a timer that is due in the future
        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) + timedelta(days=1),
            scope_name='user',
            scope_context={'range': 1}
        )

        poll_and_execute_timers()

        # fetch the timer again from DB
        updated_timer = self.store.get_notification_timer(timer.name)

        # should not have executed
        self.assertIsNone(updated_timer.executed_at)

        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(days=1),
            scope_name='user',
            scope_context={'user_id': 1},
            timer_name=timer.name
        )

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        self.assertIsNotNone(updated_timer.executed_at)
        self.assertIsNone(updated_timer.err_msg)

        # assert we now have a notification due to the timer executing
        self.assertEquals(self.store.get_num_notifications_for_user(1), 1)

    def test_cancel_timer(self):
        """
        Make sure we a cancel a timer
        """

        # set up a timer that is due in the past
        timer = publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(days=1),
            scope_name='user',
            scope_context={'range': 1}
        )

        cancel_timed_notification(timer.name)

        # fetch the timer again from DB
        updated_timer = self.store.get_notification_timer(timer.name)

        # is_active = False
        self.assertFalse(updated_timer.is_active)

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        # should not have been executed
        self.assertIsNone(updated_timer.executed_at)

    def test_update_timer_past_due(self):
        """
        Make sure if we register a timer, update it so that it is in the past,
        that the original timer is cancelled
        """

        # set up a timer that is due in the future
        publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) + timedelta(days=1),
            scope_name='user',
            scope_context={'range': 1},
            timer_name='test-timer',
            ignore_if_past_due=True
        )

        # now update it so that it is in the past
        publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) - timedelta(days=1),
            scope_name='user',
            scope_context={'range': 1},
            timer_name='test-timer',
            ignore_if_past_due=True
        )

        # fetch the timer from the DB
        timer = self.store.get_notification_timer('test-timer')

        # should not be active, the the update operation should
        # have marked it as cancelled
        self.assertFalse(timer.is_active)

        poll_and_execute_timers()

        # fetch the timer from the DB as it should be updated
        updated_timer = self.store.get_notification_timer(timer.name)

        # should not have been executed
        self.assertIsNone(updated_timer.executed_at)

        # now, re-edit and put back to the future
        publish_timed_notification(
            msg=self.msg,
            send_at=datetime.now(pytz.UTC) + timedelta(days=1),
            scope_name='user',
            scope_context={'range': 1},
            timer_name='test-timer',
            ignore_if_past_due=True
        )

        # fetch the timer from the DB
        timer = self.store.get_notification_timer('test-timer')

        # should  be active again
        self.assertTrue(timer.is_active)

    def test_cancel_non_existing_timer(self):
        """
        Make sure canceling a time that does not exist raises a ItemNotFoundError
        """

        raised = False

        try:
            cancel_timed_notification('no-exist')
        except ItemNotFoundError:
            raised = True

        self.assertFalse(raised)


class DigestNotificationsTests(TestCase):
    """
    Tests the creating of digest notifications
    """

    def setUp(self):
        """
        start up stuff
        """
        startup.initialize()
        self.daily_digest_timer_name = 'daily-digest-timer'
        self.weekly_digest_timer_name = 'weekly-digest-timer'
        self.store = notification_store()

    def test_digest_timers_registered(self):
        """
        test to check for daily and weekly digest timers are registered
        """
        self.assertIsNotNone(self.store.get_notification_timer(self.daily_digest_timer_name))
        self.assertIsNotNone(self.store.get_notification_timer(self.weekly_digest_timer_name))

    def test_daily_digest_timers(self):
        """
        test to check for daily digest timers calling back each day
        """
        daily_digest_timer = self.store.get_notification_timer(self.daily_digest_timer_name)
        previous_callback_at = daily_digest_timer.callback_at
        background_notification_check.Command().handle()

        # fetch the timer from the DB as it should be updated
        daily_digest_timer = self.store.get_notification_timer(self.daily_digest_timer_name)
        current_callback_at = daily_digest_timer.callback_at

        self.assertIsNone(daily_digest_timer.executed_at)
        self.assertEqual(previous_callback_at, current_callback_at)

        # now reset the time to 1 day from now in future
        #  in order to execute the daily digest timer again
        reset_time = datetime.now(pytz.UTC) + timedelta(days=1)
        with freeze_time(reset_time):
            # call digest command handle again
            background_notification_check.Command().handle()
            # fetch the timer from the DB as it should be updated
            daily_digest_timer = self.store.get_notification_timer(self.daily_digest_timer_name)

            self.assertIn('last_ran', daily_digest_timer.context)
            self.assertTrue(isinstance(daily_digest_timer.context['last_ran'], datetime))
            self.assertTrue(daily_digest_timer.context['last_ran'] - reset_time < timedelta(seconds=1))

            freeze_time_callback_at = daily_digest_timer.callback_at
            self.assertIsNone(daily_digest_timer.executed_at)
            self.assertEqual(current_callback_at, freeze_time_callback_at - timedelta(days=1))

        # now reset the time 1 more day in future
        # in order to execute the daily digest timer again
        reset_time = reset_time + timedelta(days=1)
        current_callback_at = daily_digest_timer.callback_at
        with freeze_time(reset_time):
            # call digest command handle again
            background_notification_check.Command().handle()
            # fetch the timer from the DB as it should be updated
            daily_digest_timer = self.store.get_notification_timer(self.daily_digest_timer_name)

            self.assertIn('last_ran', daily_digest_timer.context)
            self.assertTrue(isinstance(daily_digest_timer.context['last_ran'], datetime))
            self.assertTrue(daily_digest_timer.context['last_ran'] - reset_time < timedelta(seconds=1))

            freeze_time_callback_at = daily_digest_timer.callback_at
            self.assertIsNone(daily_digest_timer.executed_at)
            self.assertEqual(current_callback_at, freeze_time_callback_at - timedelta(days=1))

    def test_weekly_digest_timers(self):
        """
        test to check for weekly digest timers calling back each week
        """
        weekly_digest_timer_name = self.store.get_notification_timer(self.weekly_digest_timer_name)
        previous_callback_at = weekly_digest_timer_name.callback_at
        background_notification_check.Command().handle()

        # fetch the timer from the DB as it should be updated
        weekly_digest_timer_name = self.store.get_notification_timer(self.weekly_digest_timer_name)
        current_callback_at = weekly_digest_timer_name.callback_at

        self.assertIsNone(weekly_digest_timer_name.executed_at)
        self.assertEqual(previous_callback_at, current_callback_at)

        # now reset the time to 7 days(1 Week) from now in future
        #  in order to execute the daily digest timer again
        reset_time = datetime.now(pytz.UTC) + timedelta(days=7)
        with freeze_time(reset_time):
            # call digest command handle again
            background_notification_check.Command().handle()
            # fetch the timer from the DB as it should be updated
            weekly_digest_timer_name = self.store.get_notification_timer(self.weekly_digest_timer_name)

            self.assertIn('last_ran', weekly_digest_timer_name.context)
            self.assertTrue(isinstance(weekly_digest_timer_name.context['last_ran'], datetime))
            self.assertTrue(weekly_digest_timer_name.context['last_ran'] - reset_time < timedelta(seconds=1))

            freeze_time_callback_at = weekly_digest_timer_name.callback_at
            self.assertIsNone(weekly_digest_timer_name.executed_at)
            self.assertEqual(current_callback_at, freeze_time_callback_at - timedelta(days=7))


class PurgeNotificationsTests(TestCase):
    """
    Tests the purging of old notifications.
    """

    def setUp(self):
        """
        start up stuff
        """
        startup.initialize()
        self.purge_notifications_timer_name = 'purge-notifications-timer'
        self.store = notification_store()

    def test_purge_timer_registered(self):
        """
        Test if the purge notifications timer has been registered.
        """
        self.assertIsNotNone(self.store.get_notification_timer(self.purge_notifications_timer_name))

    def test_purge_timer_rescheduling(self):
        """
        Tests if the purge timer is rescheduled every day.
        """
        purge_notifications_timer = self.store.get_notification_timer(self.purge_notifications_timer_name)
        previous_callback_at = purge_notifications_timer.callback_at
        background_notification_check.Command().handle()

        # Fetch the timer again since it should be updated.
        purge_notifications_timer = self.store.get_notification_timer(self.purge_notifications_timer_name)
        current_callback_at = purge_notifications_timer.callback_at

        self.assertIsNone(purge_notifications_timer.executed_at)
        self.assertEqual(previous_callback_at, current_callback_at)

        # now reset the time to 1 day from now in future
        #  in order to execute the daily digest timer again
        reset_time = (datetime.now(pytz.UTC) + timedelta(days=1)).replace(hour=1, minute=0, second=0)
        with freeze_time(reset_time):
            # call digest command handle again
            background_notification_check.Command().handle()
            # fetch the timer from the DB as it should be updated
            purge_notifications_timer = self.store.get_notification_timer(self.purge_notifications_timer_name)
            self.assertIsNone(purge_notifications_timer.executed_at)

            # allow for some slight time arthimetic skew
            expected_callback_at = purge_notifications_timer.callback_at.replace(second=0, microsecond=0)
            actual_callback_at = (reset_time + timedelta(days=1)).replace(second=0, microsecond=0)

            self.assertEqual(expected_callback_at, actual_callback_at)
