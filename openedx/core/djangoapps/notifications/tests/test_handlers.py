"""
Tests for the `generate_user_notifications` signal handler.
"""
import unittest
from unittest.mock import patch

from openedx_events.learning.data import UserNotificationData
from openedx_events.learning.signals import USER_NOTIFICATION


class TestGenerateUserNotifications(unittest.TestCase):
    """
    Tests for the `generate_user_notifications` signal handler.
    """

    def test_generate_user_notifications_is_called_when_user_notification_signal_is_sent(self):
        # Create a UserNotificationData object.
        with patch('openedx.core.djangoapps.notifications.tasks.send_notifications') as send_notifications_mock:
            send_notifications_mock.return_value = False
            notification_data = UserNotificationData(
                user_ids=[1],
                notification_type='new_comment',
                content_url='http://example.com',
                app_name='discussion',
                course_key='course-v1:edX+DemoX+Demo_Course',
                context={'course_id': 'course-v1:edX+DemoX+Demo_Course'},
            )

            # Send the USER_NOTIFICATION signal.
            USER_NOTIFICATION.send_event(notification_data=notification_data)

            # Verify that the `send_notifications` task was called with the correct arguments.
            send_notifications_mock.assert_called_with(
                user_ids=[1],
                notification_type='new_comment',
                content_url='http://example.com',
                app_name='discussion',
                course_key='course-v1:edX+DemoX+Demo_Course',
                context={'course_id': 'course-v1:edX+DemoX+Demo_Course'}
            )
