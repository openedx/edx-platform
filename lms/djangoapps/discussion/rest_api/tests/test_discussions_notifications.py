"""
Unit tests for the DiscussionNotificationSender class
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from edx_toggles.toggles.testutils import override_waffle_flag

from lms.djangoapps.discussion.rest_api.discussions_notifications import DiscussionNotificationSender
from lms.djangoapps.discussion.toggles import ENABLE_REPORTED_CONTENT_NOTIFICATIONS


@patch('lms.djangoapps.discussion.rest_api.discussions_notifications.DiscussionNotificationSender'
       '._create_cohort_course_audience', return_value={})
@patch('lms.djangoapps.discussion.rest_api.discussions_notifications.DiscussionNotificationSender'
       '._send_course_wide_notification')
@pytest.mark.django_db
class TestDiscussionNotificationSender(unittest.TestCase):
    """
    Tests for the DiscussionNotificationSender class
    """

    @override_waffle_flag(ENABLE_REPORTED_CONTENT_NOTIFICATIONS, True)
    def setUp(self):
        self.thread = MagicMock()
        self.course = MagicMock()
        self.creator = MagicMock()
        self.notification_sender = DiscussionNotificationSender(self.thread, self.course, self.creator)

    def _setup_thread(self, thread_type, body, depth):
        """
        Helper to set up the thread object
        """
        self.thread.type = thread_type
        self.thread.body = body
        self.thread.depth = depth
        self.creator.username = 'test_user'

    def _assert_send_notification_called_with(self, mock_send_notification, expected_content_type):
        """
        Helper to assert that the send_notification method was called with the correct arguments
        """
        notification_type, audience_filters, context = mock_send_notification.call_args[0]
        mock_send_notification.assert_called_once()

        self.assertEqual(notification_type, "content_reported")
        self.assertEqual(context, {
            'username': 'test_user',
            'content_type': expected_content_type,
            'content': 'Thread body'
        })
        self.assertEqual(audience_filters, {
            'discussion_roles': ['Administrator', 'Moderator', 'Community TA']
        })
        self.assertEqual(len(audience_filters), 1)
        self.assertEqual(list(audience_filters.keys()), ['discussion_roles'])

    def test_send_reported_content_notification_for_response(self, mock_send_notification, mock_create_audience):
        """
        Test that the send_reported_content_notification method calls the send_notification method with the correct
        arguments for a comment with depth 0
        """
        self._setup_thread('comment', '<p>Thread body</p>', 0)
        mock_create_audience.return_value = {}

        self.notification_sender.send_reported_content_notification()

        self._assert_send_notification_called_with(mock_send_notification, 'response')

    def test_send_reported_content_notification_for_comment(self, mock_send_notification, mock_create_audience):
        """
        Test that the send_reported_content_notification method calls the send_notification method with the correct
        arguments for a comment with depth 1
        """
        self._setup_thread('comment', '<p>Thread body</p>', 1)
        mock_create_audience.return_value = {}

        self.notification_sender.send_reported_content_notification()

        self._assert_send_notification_called_with(mock_send_notification, 'comment')

    def test_send_reported_content_notification_for_thread(self, mock_send_notification, mock_create_audience):
        """
        Test that the send_reported_content_notification method calls the send_notification method with the correct
        """
        self._setup_thread('thread', '<p>Thread body</p>', 0)
        mock_create_audience.return_value = {}

        self.notification_sender.send_reported_content_notification()

        self._assert_send_notification_called_with(mock_send_notification, 'thread')
