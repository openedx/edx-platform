"""
Unit tests for parse_push.py
"""

import pytz
from datetime import datetime, timedelta
from mock import patch
from django.test import TestCase

from edx_notifications.channels.parse_push import (
    ParsePushNotificationChannelProvider,
    _PARSE_SERVICE_USER_ID,
)

from edx_notifications.lib.publisher import (
    register_notification_type,
)

from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
)
from edx_notifications.timer import poll_and_execute_timers
from edx_notifications.exceptions import ChannelError

from edx_notifications import startup

from parse_rest.core import ParseError


class MockCrashingParsePush(object):
    """
    Simulate an exception
    """
    def alert(self, data=None, channels=None):  # pylint: disable=unused-argument
        """
        Implement the interface, but just raise the ParseError exception
        """
        raise ParseError('oops')


class ParsePushTestCases(TestCase):
    """
    Unit tests for the ParsePushNotificationChannelProvider
    """

    def setUp(self):
        """
        Test setup
        """

        startup.initialize(register_system_types=False)

        self.msg_type = NotificationType(
            name='open-edx.edx_notifications.lib.tests.test_publisher',
            renderer='edx_notifications.renderers.basic.JsonRenderer',
        )
        register_notification_type(self.msg_type)

        self.msg = NotificationMessage(
            namespace='test-runner',
            msg_type=self.msg_type,
            payload={
                'foo': 'bar',
                'one': 'two'
            }
        )

    def test_bad_values(self):
        """
        Test error conditions
        """

        # missing __init__ args
        with self.assertRaises(Exception):
            ParsePushNotificationChannelProvider()

        with self.assertRaises(Exception):
            ParsePushNotificationChannelProvider(application_id='foo')

        with self.assertRaises(Exception):
            ParsePushNotificationChannelProvider(rest_api_key='bar')

        # create instance with proper __init__ params
        channel = ParsePushNotificationChannelProvider(application_id='foo', rest_api_key='bar')

        # bad user_id
        with self.assertRaises(ValueError):
            channel.dispatch_notification_to_user(0, self.msg)

        # missing channel context
        with self.assertRaises(ValueError):
            channel.dispatch_notification_to_user(_PARSE_SERVICE_USER_ID, self.msg, None)

        # missing parse_channel_ids
        with self.assertRaises(ValueError):
            channel.dispatch_notification_to_user(_PARSE_SERVICE_USER_ID, self.msg, {})

        # bad type of parse_channel_ids
        with self.assertRaises(TypeError):
            channel.dispatch_notification_to_user(_PARSE_SERVICE_USER_ID, self.msg, {'parse_channel_ids': 'foo'})

    def test_resolve_msg_link(self):
        """
        Make sure that resolve_msg_link returns None, because it is not applicable
        """
        channel = ParsePushNotificationChannelProvider(application_id='foo', rest_api_key='bar')
        self.assertIsNone(
            channel.resolve_msg_link(
                self.msg,
                'link',
                {}
            )
        )

    @patch("edx_notifications.channels.parse_push.Push")
    def test_publish_notification(self, mock_parse_push):
        """
        Happy path testing of a push notification
        """

        ParsePushNotificationChannelProvider.publish_notification(
            'test-runner',
            'test-type',
            {
                'foo': 'bar',
                'one': 'two'
            },
            ['test_channel_id']
        )
        self.assertTrue(mock_parse_push.alert.called)
        mock_parse_push.alert.assert_called_with(data=self.msg.payload, channels=['test_channel_id'])

    @patch("edx_notifications.channels.parse_push.Push")
    def test_bulk_publish_notification(self, mock_parse_push):
        """
        Happy path testing of a bulk push notification
        """
        channel = ParsePushNotificationChannelProvider(application_id='foo', rest_api_key='bar')

        channel.bulk_dispatch_notification(
            [_PARSE_SERVICE_USER_ID],
            self.msg,
            channel_context={
                'parse_channel_ids': ['test_channel_id']
            }
        )
        self.assertTrue(mock_parse_push.alert.called)
        mock_parse_push.alert.assert_called_with(data=self.msg.payload, channels=['test_channel_id'])

    @patch("edx_notifications.channels.parse_push.Push")
    def test_publish_timed_notification(self, mock_parse_push):
        """
        Happy path testing of a push notification that is put on a timer
        """

        send_at = datetime.now(pytz.UTC) - timedelta(days=1)

        ParsePushNotificationChannelProvider.publish_notification(
            'test-runner',
            'test-type',
            {
                'foo': 'bar',
                'one': 'two'
            },
            ['test_channel_id'],
            send_at=send_at
        )

        # force the timer to execute
        poll_and_execute_timers()

        # Parse should have been called
        self.assertTrue(mock_parse_push.alert.called)
        mock_parse_push.alert.assert_called_with(data=self.msg.payload, channels=['test_channel_id'])

    @patch("edx_notifications.channels.parse_push.Push", MockCrashingParsePush())
    def test_parse_exception(self):
        """
        Make sure we can handle a simualted exception from Parse
        """

        with self.assertRaises(ChannelError):
            ParsePushNotificationChannelProvider.publish_notification(
                'test-runner',
                'test-type',
                {
                    'foo': 'bar',
                    'one': 'two'
                },
                ['test_channel_id']
            )
