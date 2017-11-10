"""
Specific tests for the models.py file
"""

from django.test import TestCase

from edx_notifications.stores.sql.models import (
    SQLNotificationMessage,
    SQLNotificationType,
    SQLUserNotification, SQLUserNotificationArchive)

from edx_notifications.data import (
    NotificationMessage,
    NotificationType
)


class SQLModelsTests(TestCase):
    """
    Test cases for the models.py classes
    """

    def test_from_data_object(self):
        """
        Make sure we can hydrate a SQLNotificationMessage from a NotificationMessage
        """

        msg_type = NotificationType(
            name='foo.bar.baz',
            renderer='foo.renderer',
        )

        msg = NotificationMessage(
            id=2,
            msg_type=msg_type
        )

        orm_obj = SQLNotificationMessage.from_data_object(msg)

        self.assertEqual(orm_obj.id, msg.id)

    def test_to_data_object(self):
        """
        Test that we can create a NotificationMessage from a SQLNotificationMessage
        """
        orm_obj = SQLNotificationMessage(
            id=1,
            msg_type=SQLNotificationType()
        )

        msg = orm_obj.to_data_object()
        self.assertIsNotNone(msg)

    def test_user_notification_model_has_all_fields_of_archive_user_notification_model(self):
        """
        Test to check that the SQLUserNotification Model has all the fields (names) of
        the SQLUserNotificationArchive model.
        """
        user_notification = SQLUserNotification()
        user_notification_archive = SQLUserNotificationArchive()
        for archive_attr in user_notification_archive.__dict__.keys():
            self.assertIn(archive_attr, user_notification.__dict__.keys())

    def test_archive_user_notification_model_has_all_fields_of_user_notification_model(self):
        """
        Test to check that the SQLUserNotificationArchive Model has all the fields (names) of
        the SQLUserNotification model.
        """
        user_notification_orig = SQLUserNotification()
        user_notification_archive = SQLUserNotificationArchive()
        for orig_attr in user_notification_orig.__dict__.keys():
            self.assertIn(orig_attr, user_notification_archive.__dict__.keys())
