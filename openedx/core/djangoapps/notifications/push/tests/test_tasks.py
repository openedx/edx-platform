"""
Tests for push notifications tasks.
"""
from unittest import mock

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications.push.tasks import send_ace_msg_to_push_channel
from openedx.core.djangoapps.notifications.tests.utils import create_notification
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class SendNotificationsTest(ModuleStoreTestCase):
    """
    Tests for send_notifications.
    """

    def setUp(self):
        """
        Create a course and users for the course.
        """

        super().setUp()
        self.user_1 = UserFactory()
        self.user_2 = UserFactory()
        self.course_1 = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        self.notification = create_notification(
            self.user, self.course_1.id, app_name='discussion', notification_type='new_comment'
        )

    @mock.patch('openedx.core.djangoapps.notifications.push.tasks.ace.send')
    def test_send_ace_msg_success(self, mock_ace_send):
        """ Test send_ace_msg_success """
        send_ace_msg_to_push_channel(
            [self.user_1.id, self.user_2.id],
            self.notification,
            sender_id=self.user_1.id
        )

        mock_ace_send.assert_called_once()
        message_sent = mock_ace_send.call_args[0][0]
        assert message_sent.options['emails'] == [self.user_1.email, self.user_2.email]
        assert message_sent.options['braze_campaign'] == 'new_comment'

    @mock.patch('openedx.core.djangoapps.notifications.push.tasks.ace.send')
    def test_send_ace_msg_no_sender(self, mock_ace_send):
        """ Test when sender is not valid """
        send_ace_msg_to_push_channel(
            [self.user_1.id, self.user_2.id],
            self.notification,
            sender_id=999
        )

        mock_ace_send.assert_called_once()

    @mock.patch('openedx.core.djangoapps.notifications.push.tasks.ace.send')
    def test_send_ace_msg_empty_audience(self, mock_ace_send):
        """ Test send_ace_msg_success with empty audience """
        send_ace_msg_to_push_channel([], self.notification, sender_id=self.user_1.id)
        mock_ace_send.assert_not_called()

    @mock.patch('openedx.core.djangoapps.notifications.push.tasks.ace.send')
    def test_send_ace_msg_non_discussion_app(self, mock_ace_send):
        """ Test send_ace_msg_success with non-discussion app """
        self.notification.app_name = 'ecommerce'
        self.notification.save()
        send_ace_msg_to_push_channel([1], self.notification, sender_id=self.user_1.id)
        mock_ace_send.assert_not_called()
