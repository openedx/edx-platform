"""
Tests for notification grouping module
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pytz import utc

from openedx.core.djangoapps.notifications.grouping_notifications import (
    BaseNotificationGrouper,
    NotificationRegistry,
    NewCommentGrouper,
    group_user_notifications,
    get_user_existing_notifications
)
from openedx.core.djangoapps.notifications.models import Notification


class TestNotificationRegistry(unittest.TestCase):
    """
    Tests for the NotificationRegistry class
    """

    def test_register_and_get_grouper(self):
        """
        Test that the register and get_grouper methods work as expected
        """

        class TestGrouper(BaseNotificationGrouper):
            def group(self, new_notification, old_notification):
                pass

        NotificationRegistry.register('test_notification')(TestGrouper)
        grouper = NotificationRegistry.get_grouper('test_notification')
        self.assertIsInstance(grouper, TestGrouper)

    def test_get_grouper_returns_none_for_unregistered_type(self):
        """
        Test that get_grouper returns None for an unregistered notification type
        """
        grouper = NotificationRegistry.get_grouper('non_existent')
        self.assertIsNone(grouper)


class TestNewCommentGrouper(unittest.TestCase):
    """
    Tests for the NewCommentGrouper class
    """

    def setUp(self):
        """
        Set up the test
        """
        self.new_notification = MagicMock(spec=Notification)
        self.old_notification = MagicMock(spec=Notification)
        self.old_notification.content_context = {
            'replier_name': 'User1'
        }

    def test_group_creates_grouping_keys(self):
        """
        Test that the function creates the grouping keys
        """
        updated_context = NewCommentGrouper().group(self.new_notification, self.old_notification)

        self.assertIn('replier_name_list', updated_context)
        self.assertIn('grouped_count', updated_context)
        self.assertEqual(updated_context['grouped_count'], 2)
        self.assertTrue(updated_context['grouped'])

    def test_group_appends_to_existing_grouping(self):
        """
        Test that the function appends to the existing grouping
        """
        # Mock a pre-grouped notification
        self.old_notification.content_context = {
            'replier_name': 'User1',
            'replier_name_list': ['User1', 'User2'],
            'grouped': True,
            'grouped_count': 2
        }
        self.new_notification.content_context = {'replier_name': 'User3'}

        updated_context = NewCommentGrouper().group(self.new_notification, self.old_notification)

        self.assertIn('replier_name_list', updated_context)
        self.assertEqual(len(updated_context['replier_name_list']), 3)
        self.assertEqual(updated_context['grouped_count'], 3)


class TestGroupUserNotifications(unittest.TestCase):
    """
    Tests for the group_user_notifications function
    """

    @patch('openedx.core.djangoapps.notifications.grouping_notifications.NotificationRegistry.get_grouper')
    def test_group_user_notifications(self, mock_get_grouper):
        """
        Test that the function groups notifications using the appropriate grou
        """
        # Mock the grouper
        mock_grouper = MagicMock(spec=NewCommentGrouper)
        mock_get_grouper.return_value = mock_grouper

        new_notification = MagicMock(spec=Notification)
        old_notification = MagicMock(spec=Notification)

        group_user_notifications(new_notification, old_notification)

        mock_grouper.group.assert_called_once_with(new_notification, old_notification)
        self.assertTrue(old_notification.save.called)
        self.assertIsNone(old_notification.last_read)
        self.assertIsNone(old_notification.last_seen)
        self.assertIsNotNone(old_notification.created)

    def test_group_user_notifications_no_grouper(self):
        """
        Test that the function does nothing if no grouper is found
        """
        new_notification = MagicMock(spec=Notification)
        old_notification = MagicMock(spec=Notification)

        group_user_notifications(new_notification, old_notification)

        self.assertFalse(old_notification.save.called)


class TestGetUserExistingNotifications(unittest.TestCase):
    """
    Tests for the get_user_existing_notifications function
    """

    @patch('openedx.core.djangoapps.notifications.models.Notification.objects.filter')
    def test_get_user_existing_notifications(self, mock_filter):
        """
        Test that the function returns the last notification for each user
        """
        # Mock the notification objects returned by the filter
        mock_notification1 = MagicMock(spec=Notification)
        mock_notification1.user_id = 1
        mock_notification1.created = datetime(2023, 9, 1, tzinfo=utc)

        mock_notification2 = MagicMock(spec=Notification)
        mock_notification2.user_id = 1
        mock_notification2.created = datetime(2023, 9, 2, tzinfo=utc)

        mock_filter.return_value = [mock_notification1, mock_notification2]

        user_ids = [1, 2]
        notification_type = 'new_comment'
        group_by_id = 'group_id_1'
        course_id = 'course_1'

        result = get_user_existing_notifications(user_ids, notification_type, group_by_id, course_id)

        # Verify the results
        self.assertEqual(result[1], mock_notification1)
        self.assertIsNone(result[2])  # user 2 has no notifications
