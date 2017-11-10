"""
Test cases for UA API
"""
from mock import patch

from django.test import TestCase

from edx_notifications import startup
from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
)
from edx_notifications.lib.publisher import (
    register_notification_type,
)
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    bulk_publish_notification_to_users,
)
from testserver.views import CANNED_TEST_PAYLOAD


class UrbanAirTestCases(TestCase):
    """
    Test cases for urban airship channel
    """
    def setUp(self):
        """
        Sets up test environments
        """
        startup.initialize()
        self.msg_type = NotificationType(
            name='open-edx.studio.announcements.new-announcement',
            renderer='edx_notifications.openedx.course_announcements.NewCourseAnnouncementRenderer'
        )
        register_notification_type(self.msg_type)
        self.msg = NotificationMessage(
            namespace='foo/bar/baz',
            msg_type=self.msg_type,
            payload=CANNED_TEST_PAYLOAD['open-edx.studio.announcements.new-announcement']
        )

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_tag_group_notification(self, mock_ua_push_api):
        """
        Test publish notification to a tag group
        :return:
        """
        mock_ua_push_api.return_value = {'ok': 'true'}
        self.msg.payload['open_url'] = 'http://example.com'
        self.msg.payload['tag_group'] = 'enrollments'
        response = bulk_publish_notification_to_users([], self.msg, preferred_channel='urban-airship')
        self.assertTrue(response)
        self.assertEqual(response['ok'], 'true')

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_bulk_user_notification(self, mock_ua_push_api):
        """
        Test publish notification to list of users
        :return:
        """
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = bulk_publish_notification_to_users([10, 11, 12], self.msg, preferred_channel='urban-airship')
        self.assertEqual(response['ok'], 'true')

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_single_user_notification(self, mock_ua_push_api):
        """
        Test publish notification to a single user
        :return:
        """
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = publish_notification_to_user(10, self.msg, preferred_channel='urban-airship')
        self.assertEqual(response['ok'], 'true')
