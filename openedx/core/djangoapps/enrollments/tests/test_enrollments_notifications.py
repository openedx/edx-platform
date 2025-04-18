"""
Unit tests for the EnrollmentsNotificationSender class
"""
import unittest
import datetime
from unittest.mock import MagicMock, patch

from django.conf import settings
import pytest

from openedx.core.djangoapps.enrollments.enrollments_notifications import EnrollmentNotificationSender
from openedx_events.learning.data import UserNotificationData


@pytest.mark.django_db
class TestEnrollmentsNotificationSender(unittest.TestCase):
    """
    Tests for the EnrollmentsNotificationSender class
    """

    def setUp(self):
        self.course = MagicMock()
        self.course.name = "test course"
        self.course.id = 1
        self.expiry_date = datetime.date.today() + datetime.timedelta(days=1)
        self.user_id = '123'
        self.notification_sender = EnrollmentNotificationSender(self.course, self.user_id, self.expiry_date)


    @patch('openedx.core.djangoapps.enrollments.enrollments_notifications.USER_NOTIFICATION_REQUESTED.send_event')
    def test_send_audit_access_expiring_soon_notification(self, mock_send_notification):
        """
        Test that audit access expiring soon notification event is sent with correct parameters.
        """

        self.notification_sender.send_audit_access_expiring_soon_notification()

        mock_send_notification.assert_called_once()
        notification_data = UserNotificationData(
            user_ids=[int(self.user_id)],
            context={
                'course': self.course.name,
                'audit_access_expiry': self.expiry_date,
            },
            notification_type='audit_access_expiring_soon',
            content_url=f"{settings.LEARNING_MICROFRONTEND_URL}/course/{str(self.course.id)}/home",
            app_name="enrollments",
            course_key=self.course.id,
        )
        mock_send_notification.assert_called_with(notification_data=notification_data)
