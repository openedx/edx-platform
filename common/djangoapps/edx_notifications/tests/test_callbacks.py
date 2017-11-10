"""
Tests for the callback.py
"""

from django.test import TestCase

from edx_notifications.data import (
    NotificationCallbackTimer,
    NotificationMessage,
    NotificationType,
)
from edx_notifications.tests.test_scopes import TestListScopeResolver
from edx_notifications.scopes import register_user_scope_resolver
from edx_notifications.callbacks import NotificationDispatchMessageCallback
from edx_notifications.stores.store import notification_store


class CallbackTests(TestCase):
    """
    Tests for callback.py
    """

    def setUp(self):
        """
        start up stuff
        """

        register_user_scope_resolver('list_scope', TestListScopeResolver())

        self.store = notification_store()
        self.callback = NotificationDispatchMessageCallback()

        self.msg_type = self.store.save_notification_type(
            NotificationType(
                name='foo.bar',
                renderer='foo',
            )
        )

        self.msg = self.store.save_notification_message(
            NotificationMessage(
                msg_type=self.msg_type,
                payload={'foo': 'bar'},
            )
        )

        self.timer_for_user = NotificationCallbackTimer(
            context={
                'msg_id': self.msg.id,
                'distribution_scope': {
                    'scope_name': 'user',
                    'scope_context': {
                        'user_id': 1
                    }
                }
            }
        )

        self.timer_for_group = NotificationCallbackTimer(
            context={
                'msg_id': self.msg.id,
                'distribution_scope': {
                    'scope_name': 'list_scope',
                    'scope_context': {
                        'range': 5
                    }
                }
            }
        )

    def test_execute_callback(self):
        """
        Happy path test to execute the timer callback, which
        should dispatch notifications
        """

        # assert we have no notifications
        self.assertEquals(self.store.get_num_notifications_for_user(1), 0)

        results = self.callback.notification_timer_callback(self.timer_for_user)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 1)
        self.assertEqual(len(results['errors']), 0)
        self.assertIsNone(results['reschedule_in_mins'])

        # assert we now have a notification
        self.assertEquals(self.store.get_num_notifications_for_user(1), 1)

    def test_execute_scoped_callback(self):
        """
        Happy path test to execute the timer callback, which
        should dispatch notifications
        """

        # assert we have no notifications
        for user_id in range(self.timer_for_group.context['distribution_scope']['scope_context']['range']):
            self.assertEquals(self.store.get_num_notifications_for_user(user_id), 0)

        results = self.callback.notification_timer_callback(self.timer_for_group)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 5)
        self.assertEqual(len(results['errors']), 0)
        self.assertIsNone(results['reschedule_in_mins'])

        # assert we now have a notification
        for user_id in range(self.timer_for_group.context['distribution_scope']['scope_context']['range']):
            self.assertEquals(self.store.get_num_notifications_for_user(user_id), 1)

    def test_bad_context(self):
        """
        Test missing context parameter
        """
        bad_timer = NotificationCallbackTimer(
            context={
                # missing msg_id
                'distribution_scope': {
                    'scope_name': 'user',
                    'scope_context': {
                        'user_id': 1
                    }
                }
            }
        )

        results = self.callback.notification_timer_callback(bad_timer)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIsNone(results['reschedule_in_mins'])

        bad_timer = NotificationCallbackTimer(
            context={
                'msg_id': self.msg.id,
                'distribution_scope': {
                    'scope_name': 'user',
                    'scope_context': {
                        # missing user_id
                    }
                }
            }
        )

        results = self.callback.notification_timer_callback(bad_timer)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIsNone(results['reschedule_in_mins'])

    def test_cant_find_msg(self):
        """
        Test timer that points to a non-existing msg
        """
        bad_timer = NotificationCallbackTimer(
            context={
                'msg_id': 9999,
                'distribution_scope': {
                    'scope_name': 'user',
                    'scope_context': {
                        'user_id': 1
                    }
                }
            }
        )

        results = self.callback.notification_timer_callback(bad_timer)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIsNone(results['reschedule_in_mins'])

    def test_cant_no_scope(self):
        """
        Asserts that if a scope cannot be resolved, then nothing is sent
        """

        self.timer_for_group.context['distribution_scope']['scope_name'] = 'nonexisting'

        results = self.callback.notification_timer_callback(self.timer_for_group)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIsNone(results['reschedule_in_mins'])

        register_user_scope_resolver('nonexisting', TestListScopeResolver())

        results = self.callback.notification_timer_callback(self.timer_for_group)

        self.assertIsNotNone(results)
        self.assertEqual(results['num_dispatched'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIsNone(results['reschedule_in_mins'])
