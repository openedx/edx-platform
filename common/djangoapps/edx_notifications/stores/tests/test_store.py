"""
Exercises tests on the base_store_provider file
"""

from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured

from edx_notifications.stores.store import (
    BaseNotificationStoreProvider,
    notification_store,
    reset_notification_store
)
from edx_notifications.stores.sql.store_provider import SQLNotificationStoreProvider


TEST_NOTIFICATION_STORE_PROVIDER = {
    "class": "edx_notifications.stores.sql.store_provider.SQLNotificationStoreProvider",
    "options": {
    }
}


class BadImplementationStoreProvider(BaseNotificationStoreProvider):
    """
    Test implementation of StoreProvider to assert that non-implementations of methods
    raises the correct methods
    """

    def purge_expired_notifications(self, purge_read_messages_older_than, purge_unread_messages_older_than):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).purge_expired_notifications(purge_read_messages_older_than,
                                                                                purge_unread_messages_older_than)

    def get_all_user_preferences_for_user(self, user_id):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_all_user_preferences_for_user(user_id)

    def save_notification_preference(self, notification_preference):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).save_notification_preference(notification_preference)

    def get_notification_preference(self, name):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_notification_preference(name)

    def get_all_user_preferences_with_name(self, name, value, offset=0, size=None):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_all_user_preferences_with_name(name, value, offset, size)

    def get_user_preference(self, user_id, name):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_user_preference(user_id, name)

    def get_all_notification_preferences(self):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_all_notification_preferences()

    def set_user_preference(self, user_preference):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).set_user_preference(user_preference)

    def get_notification_message_by_id(self, msg_id, options=None):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_notification_message_by_id(msg_id, options=options)

    def save_notification_message(self, msg):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).save_notification_message(msg)

    def save_user_notification(self, user_msg):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).save_user_notification(user_msg)

    def bulk_create_user_notification(self, user_msgs):
        """
        Fake implementation
        """
        super(BadImplementationStoreProvider, self).bulk_create_user_notification(user_msgs)

    def get_notification_type(self, name):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_notification_type(name)

    def get_all_notification_types(self):
        """
        Fake implementation of method which calls base class, which should throw NotImplementedError
        """
        super(BadImplementationStoreProvider, self).get_all_notification_types()

    def save_notification_type(self, msg_type):
        """
        Saves a new notification type, note that we do not support updates
        """
        super(BadImplementationStoreProvider, self).save_notification_type(msg_type)

    def get_num_notifications_for_user(self, user_id, filters=None):
        """
        Saves a new notification type, note that we do not support updates
        """
        super(BadImplementationStoreProvider, self).get_num_notifications_for_user(user_id, filters=filters)

    def get_notification_for_user(self, user_id, msg_id):
        """
        Get a single UserNotification for the user_id/msg_id pair
        """
        super(BadImplementationStoreProvider, self).get_notification_for_user(user_id, msg_id)

    def get_notifications_for_user(self, user_id, filters=None, options=None):
        """
        Saves a new notification type, note that we do not support updates
        """
        super(BadImplementationStoreProvider, self).get_notifications_for_user(
            user_id,
            filters=filters,
            options=options
        )

    def mark_user_notifications_read(self, user_id, filters=None):
        """
        Marks all notifications for user (with any filtering criteria) as read
        """
        super(BadImplementationStoreProvider, self).mark_user_notifications_read(
            user_id,
            filters=filters,
        )

    def save_notification_timer(self, timer):
        """
        Will save (create or update) a NotificationCallbackTimer in the
        StorageProvider
        """
        super(BadImplementationStoreProvider, self).save_notification_timer(None)

    def get_notification_timer(self, name):
        """
        Will return a single NotificationCallbackTimer
        """
        super(BadImplementationStoreProvider, self).get_notification_timer(None)

    def get_all_active_timers(self, until_time=None, include_executed=False):
        """
        Will return all active timers that are expired.

        If until_time is not passed in, then we will use our
        current system time
        """
        super(BadImplementationStoreProvider, self).get_all_active_timers(until_time=until_time)

    def get_all_namespaces(self, start_datetime=None, end_datetime=None):
        """
        This will return all unique namespaces that have been used
        """
        super(BadImplementationStoreProvider, self).get_all_namespaces()


class TestBaseNotificationDataProvider(TestCase):
    """
    Cover the NotificationDataProviderBase class
    """

    def setUp(self):
        """
        Harnessing
        """
        reset_notification_store()

    def test_cannot_create_instance(self):
        """
        NotificationDataProviderBase is an abstract class and we should not be able
        to create an instance of it
        """

        with self.assertRaises(TypeError):
            BaseNotificationStoreProvider()  # pylint: disable=abstract-class-instantiated

    @override_settings(NOTIFICATION_STORE_PROVIDER=TEST_NOTIFICATION_STORE_PROVIDER)
    def test_get_provider(self):
        """
        Makes sure we get an instance of the registered store provider
        """

        provider = notification_store()

        self.assertIsNotNone(provider)
        self.assertTrue(isinstance(provider, SQLNotificationStoreProvider))

    @override_settings(NOTIFICATION_STORE_PROVIDER=None)
    def test_missing_provider_config(self):
        """
        Make sure we are throwing exceptions on poor configuration
        """

        with self.assertRaises(ImproperlyConfigured):
            notification_store()

    @override_settings(NOTIFICATION_STORE_PROVIDER={"class": "foo"})
    def test_bad_provider_config(self):
        """
        Make sure we are throwing exceptions on poor configuration
        """

        with self.assertRaises(ImproperlyConfigured):
            notification_store()

    def test_base_methods_exceptions(self):
        """
        Asserts that all base-methods on the StoreProvider interface will throw
        an NotImplementedError
        """

        bad_provider = BadImplementationStoreProvider()

        with self.assertRaises(NotImplementedError):
            bad_provider.get_notification_message_by_id(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.save_notification_message(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.save_user_notification(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.bulk_create_user_notification(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_notification_type(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_notification_types()

        with self.assertRaises(NotImplementedError):
            bad_provider.save_notification_type(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_num_notifications_for_user(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_notifications_for_user(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.mark_user_notifications_read(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.save_notification_timer(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_notification_timer(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_active_timers()

        with self.assertRaises(NotImplementedError):
            bad_provider.get_notification_preference(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.save_notification_preference(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_notification_preferences()

        with self.assertRaises(NotImplementedError):
            bad_provider.get_user_preference(None, None)

        with self.assertRaises(NotImplementedError):
            bad_provider.set_user_preference(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_user_preferences_for_user(None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_user_preferences_with_name(None, None)

        with self.assertRaises(NotImplementedError):
            bad_provider.purge_expired_notifications(None, None)

        with self.assertRaises(NotImplementedError):
            bad_provider.get_all_namespaces()
