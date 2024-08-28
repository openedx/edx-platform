"""
Unit test for notification util
"""
import unittest
from unittest.mock import patch, Mock

from django.test import RequestFactory
from ..notifications import send_staff_grade_assigned_notification


class TestSendStaffGradeAssignedNotification(unittest.TestCase):
    """
       Unit tests for the send_staff_grade_assigned_notification function.
    """

    def setUp(self):
        """
        Set up mock request, usage_id, and submission data for testing.
        """
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/some/path/')
        self.request.user = Mock(id=1)

        self.usage_id = 'block-v1:TestX+TST+TST+type@problem+block@ora'
        self.submission = {
            'email': 'student@example.com',
            'score': {
                'pointsEarned': 10,
                'pointsPossible': 20,
            }
        }

    @patch('lms.djangoapps.ora_staff_grader.notifications.User.objects.get')
    @patch('lms.djangoapps.ora_staff_grader.notifications.UsageKey.from_string')
    @patch('lms.djangoapps.ora_staff_grader.notifications.modulestore')
    @patch('lms.djangoapps.ora_staff_grader.notifications.get_course_overview_or_none')
    @patch('lms.djangoapps.ora_staff_grader.notifications.USER_NOTIFICATION_REQUESTED.send_event')
    def test_send_notification_success(self, mock_send_event, mock_get_course_overview_or_none,
                                       mock_modulestore, mock_from_string, mock_get_user):
        """
        Test that the notification is sent when the user IDs do not match.
        """
        mock_get_user.return_value = Mock(id=2)
        mock_from_string.return_value = Mock(course_key='course-v1:TestX+TST+TST')
        mock_modulestore.return_value.get_item.return_value = Mock(display_name="ORA Assignment")
        mock_get_course_overview_or_none.return_value = Mock(display_name="Test Course")

        send_staff_grade_assigned_notification(self.request, self.usage_id, self.submission)

        mock_send_event.assert_called_once()
        args, kwargs = mock_send_event.call_args
        notification_data = kwargs['notification_data']
        self.assertEqual(notification_data.user_ids, [2])
        self.assertEqual(notification_data.context['ora_name'], 'ORA Assignment')
        self.assertEqual(notification_data.context['course_name'], 'Test Course')
        self.assertEqual(notification_data.context['points_earned'], 10)
        self.assertEqual(notification_data.context['points_possible'], 20)
        self.assertEqual(notification_data.notification_type, "ora_staff_grade_assigned")

    @patch('lms.djangoapps.ora_staff_grader.notifications.User.objects.get')
    @patch('lms.djangoapps.ora_staff_grader.notifications.UsageKey.from_string')
    @patch('lms.djangoapps.ora_staff_grader.notifications.USER_NOTIFICATION_REQUESTED.send_event')
    def test_no_notification_if_same_user(self, mock_send_event, mock_from_string, mock_get_user):
        """
        Test that no notification is sent when the user IDs match.
        """
        mock_get_user.return_value = Mock(id=1)  # Same ID as the request user
        mock_from_string.return_value = Mock(course_key='course-v1:TestX+TST+TST')

        send_staff_grade_assigned_notification(self.request, self.usage_id, self.submission)

        mock_send_event.assert_not_called()
