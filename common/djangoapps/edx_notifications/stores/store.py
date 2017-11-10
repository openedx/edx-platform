"""
Defines abstract class for the Notification Store data tier
"""

import abc

from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Cached instance of a store provider
_STORE_PROVIDER = None


def notification_store():
    """
    Returns the singleton instance of the StoreProvider that has been
    configured for this runtime. The class path should be
    set in NOTIFICATION_STORE_PROVIDER in the settings file

    NOTE: If we switch over to gevent support, we should investigate
    any potential concurrency issues
    """

    global _STORE_PROVIDER  # pylint: disable=global-statement

    if not _STORE_PROVIDER:
        config = getattr(settings, 'NOTIFICATION_STORE_PROVIDER')
        if not config:
            raise ImproperlyConfigured("Settings not configured with NOTIFICATION_STORE_PROVIDER!")

        if 'class' not in config or 'options' not in config:
            msg = (
                "Misconfigured NOTIFICATION_STORE_PROVIDER settings, "
                "must have both 'class' and 'options' keys."
            )
            raise ImproperlyConfigured(msg)

        module_path, _, name = config['class'].rpartition('.')
        class_ = getattr(import_module(module_path), name)

        _STORE_PROVIDER = class_(**config['options'])

    return _STORE_PROVIDER


def reset_notification_store():
    """
    Tears down any cached configuration. This is useful for testing.

    NOTE: If we switch over to gevent support, we should investigate
    any potential concurrency issues
    """

    global _STORE_PROVIDER  # pylint: disable=global-statement

    _STORE_PROVIDER = None


class BaseNotificationStoreProvider(object):
    """
    The base abstract class for all notifications data providers, such as MySQL/Django-ORM backed.

    IMPORTANT: NotificationStoreProvider is assumed to be a singleton, therefore there must be
    no state stored in the instance of the provider class.
    """

    # don't allow instantiation of this class, it must be subclassed
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_notification_message_by_id(self, msg_id, options=None):
        """
        Returns the notitication message (of NotificationMessage type) by primary key

        ARGS:
            - msg_id: the primary key of the NotificationMessage
            - options: dictionary of options. Possible choices:
                * 'select_related': whether to fully fetch any related objects

        RETURNS: type NotificationMessage
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_notification_message(self, msg):
        """
        Save (create or update) a notification message (of NotificationMessage type)

        ARGS:
            - msg: an instance of NotificationMessage. If the 'id' field is
                   set by the caller, then it is assumed to be an update
                   operation

        RETURNS: type NotificationMessage
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_user_notification(self, user_msg):
        """
        Create or Update the mapping of a user to a notification.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def bulk_create_user_notification(self, user_msgs):
        """
        This is an optimization for bulk creating *new* UserNotification
        objects in the database. Since we want to support fan-outs of messages,
        we may need to insert 10,000's (or 100,000's) of objects as optimized
        as possible.

        NOTE: This method cannot update existing UserNotifications, only create them
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notification_type(self, name):
        """
        This returns a NotificationType object.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_notification_types(self):
        """
        This returns all registered notification types.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_notification_type(self, msg_type):
        """
        Saves a new notification type, note that we do not support updates
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notification_for_user(self, user_id, msg_id):
        """
        Get a single UserNotification for the user_id/msg_id pair
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_num_notifications_for_user(self, user_id, filters=None):
        """
        Returns an integer count of edx_notifications. It is presumed
        that store provider implementations can make this an optimized
        query

        ARGS:
            - user_id: The id of the user
            - filters: a dict containing
                - namespace: what namespace to search (defuault None)
                - read: Whether to return read notifications (default True)
                - unread: Whether to return unread notifications (default True)
                - type_name: which type to return

        RETURNS: type list   i.e. []
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notifications_for_user(self, user_id, filters=None, options=None):
        """
        Returns a (unsorted) collection (list) of notifications for the user.

        NOTE: We will have to add paging (with sorting/filtering) in the future

        ARGS:
            - user_id: The id of the user
            - filters: a dict containing
                - namespace: what namespace to search (defuault None)
                - read: Whether to return read notifications (default True)
                - unread: Whether to return unread notifications (default True)
                - type_name: which type to return
            - options: a dict containing some optional parameters
                - limit: max number to return (up to some system defined max)
                - offset: offset into the list, to implement paging

        RETURNS: type list   i.e. []
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def mark_user_notifications_read(self, user_id, filters=None):
        """
        Marks all notifications for user (with any filtering criteria) as read
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_notification_timer(self, timer):
        """
        Will save (create or update) a NotificationCallbackTimer in the
        StorageProvider
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notification_timer(self, name):
        """
        Will return a single NotificationCallbackTimer
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_active_timers(self, until_time=None, include_executed=False):
        """
        Will return all active timers that are expired.

        If until_time is not passed in, then we will use our
        current system time
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notification_preference(self, name):
        """
        Will return a single NotificationPreference if exists
        else raises exception ItemNotFoundError
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_notification_preference(self, notification_preference):
        """
        Will save (create or update) a NotificationPreference in the
        StorageProvider
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_notification_preferences(self):  # pylint: disable=invalid-name
        """
        This returns list of all registered NotificationPreference.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_user_preference(self, user_id, name):
        """
        Will return a single UserNotificationPreference if exists
        else raises exception ItemNotFoundError
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_user_preference(self, user_preference):
        """
        Will save (create or update) a UserNotificationPreference in the
        StorageProvider
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_user_preferences_for_user(self, user_id):  # pylint: disable=invalid-name
        """
        This returns list of all UserNotificationPreference.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_user_preferences_with_name(self, name, value, offset=0, size=None):  # pylint: disable=invalid-name
        """
        Returns a list of UserPreferences objects which match name and value,
        so that we know all users that have the same preference. We need the 'offset'
        and 'size' parameters since this query could potentially be very large
        (imagine a course with 100K students in it) and we'll need the ability to page
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def purge_expired_notifications(self, purge_read_messages_older_than, purge_unread_messages_older_than):  # pylint: disable=invalid-name
        """
        Will purge all the unread and read messages that is in the
        db for a period of time.

        how long (in days) old READ and UNREAD notifications can remain in the system before being purged.

        Lack of configuration (or None) means: "don't purge ever"

        purge_read_messages_older_than: will control how old a READ message will remain in the backend

        purge_unread_messages_older_than: will control how old an UNREAD message will remain in the backend

        purge_read_messages_older_than will compare against the "read_at" column

        where as purge_unread_messages_older_than will compare against the "created" column.

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_namespaces(self, start_datetime=None, end_datetime=None):
        """
        This will return all unique namespaces that have been used
        """
        raise NotImplementedError()
