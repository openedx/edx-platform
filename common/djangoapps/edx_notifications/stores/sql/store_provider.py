"""
Concrete MySQL implementation of the data provider interface
"""

import copy
import pylru
import pytz
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from edx_notifications.stores.store import BaseNotificationStoreProvider
from edx_notifications.exceptions import (
    ItemNotFoundError,
    BulkOperationTooLarge,
)
from edx_notifications import const
from edx_notifications.stores.sql.models import (
    SQLNotificationMessage,
    SQLNotificationType,
    SQLUserNotification,
    SQLNotificationCallbackTimer,
    SQLNotificationPreference, SQLUserNotificationPreferences)


class SQLNotificationStoreProvider(BaseNotificationStoreProvider):
    """
    Concrete MySQL implementation of the abstract base class (interface)
    """

    def __init__(self, **kwargs):
        """
        Initializer

        ARGS: kwargs
            - MAX_MSG_TYPE_CACHE_SIZE: Maximum size of the LRU cache around
              msg_types
        """

        _msg_type_cache_size = kwargs.get('MAX_MSG_TYPE_CACHE_SIZE', 1024)
        self._msg_type_cache = pylru.lrucache(_msg_type_cache_size)

    def _get_notification_by_id(self, msg_id, options=None):
        """
        Helper method to get Notification Message by id
        """

        # pylint/pep8 seem to complain if defaults are set to empty dicts
        _options = options if options else {}
        select_related = _options.get('select_related', True)

        try:
            query = SQLNotificationMessage.objects
            if select_related:
                query = query.select_related()
            obj = query.get(id=msg_id)
        except ObjectDoesNotExist:
            raise ItemNotFoundError()

        return obj.to_data_object(options=options)

    def get_notification_message_by_id(self, msg_id, options=None):
        """
        For the given message id return the corresponding NotificationMessage data object
        """

        return self._get_notification_by_id(msg_id, options=options)

    def save_notification_message(self, msg):
        """
        Saves a passed in NotificationMsg data object. If 'id' is set by the caller
        it will try to update the object. If it does not exist it will throw an
        exception.

        If it is created, then the id property will be set on the NotificationMsg and returned
        """

        if msg.id:
            try:
                obj = SQLNotificationMessage.objects.get(id=msg.id)
                obj.load_from_data_object(msg)
            except ObjectDoesNotExist:
                msg = "Could not SQLNotificationMessage with ID {_id}".format(_id=msg.id)
                raise ItemNotFoundError()
        else:
            obj = SQLNotificationMessage.from_data_object(msg)

        obj.save()
        return obj.to_data_object()

    def get_notification_type(self, name):  # pylint: disable=no-self-use
        """
        This returns a NotificationType object.
        NOTE: NotificationTypes are supposed to be immutable during the
        process lifetime. New Types can be added, but not updated.
        Therefore we can memoize this function
        """

        data_object = None
        # pull from the cache, if we have it
        if name in self._msg_type_cache:
            data_object = self._msg_type_cache[name]
            return data_object

        try:
            obj = SQLNotificationType.objects.get(name=name)
        except ObjectDoesNotExist:
            raise ItemNotFoundError()

        data_object = obj.to_data_object()

        # refresh the cache
        self._msg_type_cache[name] = data_object
        return data_object

    def get_all_notification_types(self):  # pylint: disable=no-self-use
        """
        This returns a NotificationType object.
        NOTE: NotificationTypes are supposed to be immutable during the
        process lifetime. New Types can be added, but not updated.
        Therefore we can memoize this function
        """

        query = SQLNotificationType.objects.all()

        result_set = [item.to_data_object() for item in query]

        return result_set

    def save_notification_type(self, msg_type):
        """
        Create or update a notification type
        """

        try:
            obj = SQLNotificationType.objects.get(name=msg_type.name)
            obj.load_from_data_object(msg_type)
        except ObjectDoesNotExist:
            obj = SQLNotificationType.from_data_object(msg_type)

        try:
            obj.save()
        except IntegrityError:  # pylint: disable=catching-non-exception
            # there could be some concurrency between multiple processes
            # on startup, so try again
            try:
                obj.save()
            except IntegrityError:  # pylint: disable=catching-non-exception
                pass

        # remove cached entry
        if msg_type.name in self._msg_type_cache:
            del self._msg_type_cache[msg_type.name]
        return msg_type

    def _get_prepaged_notifications(self, user_id, filters=None, options=None):
        """
        Helper to set up the notifications query before paging
        is applied. WARNING: This should be used with care and to not
        iterate over this returned results set. Typically this
        will just be used to get a count()
        """

        _filters = filters if filters else {}
        _options = options if options else {}

        namespace = _filters.get('namespace')
        read = _filters.get('read', True)
        unread = _filters.get('unread', True)
        type_name = _filters.get('type_name')
        start_date = _filters.get('start_date')
        end_date = _filters.get('end_date')

        select_related = _options.get('select_related', False)

        if not read and not unread:
            raise ValueError('Bad arg combination either read or unread must be set to True')

        query = SQLUserNotification.objects.filter(user_id=user_id)

        if select_related:
            query = query.select_related()

        if namespace:
            query = query.filter(msg__namespace=namespace)

        if not (read and unread):
            if read:
                query = query.filter(read_at__isnull=False)

            if unread:
                query = query.filter(read_at__isnull=True)

        if type_name:
            query = query.filter(msg__msg_type=type_name)

        if start_date:
            query = query.filter(created__gte=start_date)

        if end_date:
            query = query.filter(created__lte=end_date)

        return query

    def _get_notifications_for_user(self, user_id, filters=None, options=None):
        """
        Helper method to set up the query to get notifications for a user
        this includes offset/limit parameters passed in OPTIONS
        """

        _filters = filters if filters else {}
        _options = options if options else {}

        query = self._get_prepaged_notifications(
            user_id,
            filters=filters,
            options=options
        )

        limit = _options.get('limit', const.NOTIFICATION_MAX_LIST_SIZE)
        offset = _options.get('offset', 0)

        # make sure passed in limit is allowed
        # as we don't want to blow up the query too large here
        if limit > const.NOTIFICATION_MAX_LIST_SIZE:
            raise ValueError('Max limit is {limit}'.format(limit=limit))

        return query[offset:offset + limit]

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

        RETURNS: integer
        """

        return self._get_prepaged_notifications(
            user_id,
            filters=filters,
        ).count()

    def get_notification_for_user(self, user_id, msg_id):
        """
        Get a single UserNotification for the user_id/msg_id pair
        """
        try:
            item = SQLUserNotification.objects.select_related().get(user_id=user_id, msg_id=msg_id)
            return item.to_data_object()
        except ObjectDoesNotExist:
            msg = (
                "Could not find msg_id '{msg_id}' for user_id '{user_id}'!"
            ).format(msg_id=msg_id, user_id=user_id)
            raise ItemNotFoundError(msg)

    def get_notifications_for_user(self, user_id, filters=None, options=None):
        """
        Returns a collection (list) of notifications for the user. This will be sorted
        most recent first.

        NOTE: We should add other sort ability (e.g. type/date to group together types)

        ARGS:
            - user_id: The id of the user
            - filters: a dict containing
                - namespace: what namespace to search (defuault None)
                - read: Whether to return read notifications (default True)
                - unread: Whether to return unread notifications (default True)
                - type_name: which type to return (default None)
            - options: a dict containing some optional parameters
                - limit: max number to return (up to some system defined max)
                - offset: offset into the list, to implement paging

        RETURNS: list   i.e. []
        """

        _options = copy.copy(options) if options else {}
        _options['select_related'] = True

        query = self._get_notifications_for_user(
            user_id,
            filters=filters,
            options=_options
        )

        result_set = [item.to_data_object() for item in query]

        return result_set

    def mark_user_notifications_read(self, user_id, filters=None):
        """
        This should mark all the user notifications as read

        ARGS:
            - user_id: The id of the user
        """

        _filters = copy.copy(filters) if filters else {}
        _filters.update({
            'read': False,
            'unread': True,
        })

        query = self._get_prepaged_notifications(
            user_id,
            filters=_filters
        )

        query.update(read_at=datetime.now(pytz.UTC))

    def save_user_notification(self, user_msg):
        """
        Create or Update the mapping of a user to a notification.
        """

        if user_msg.id:
            try:
                obj = SQLUserNotification.objects.get(id=user_msg.id)
                obj.load_from_data_object(user_msg)
            except ObjectDoesNotExist:
                msg = "Could not find SQLUserNotification with ID {_id}".format(_id=user_msg.id)
                raise ItemNotFoundError(msg)
        else:
            obj = SQLUserNotification.from_data_object(user_msg)

        obj.save()

        return obj.to_data_object()

    def bulk_create_user_notification(self, user_msgs):
        """
        This is an optimization for bulk creating *new* UserNotification
        objects in the database. Since we want to support fan-outs of messages,
        we may need to insert 10,000's (or 100,000's) of objects as optimized
        as possible.

        NOTE: this method will return None, the primary key of the user_msgs
              that was created will not be returned (limitation of Django ORM)

        NOTE: This method cannot update existing UserNotifications, only create them.
        NOTE: It is assumed that user_msgs is already chunked in an appropriate size.
        """

        if len(user_msgs) > const.NOTIFICATION_BULK_PUBLISH_CHUNK_SIZE:
            msg = (
                'You have passed in a user_msgs list of size {length} but the size '
                'limit is {max}.'.format(length=len(user_msgs), max=const.NOTIFICATION_BULK_PUBLISH_CHUNK_SIZE)
            )
            raise BulkOperationTooLarge(msg)

        objs = []
        for user_msg in user_msgs:
            objs.append(SQLUserNotification.from_data_object(user_msg))

        SQLUserNotification.objects.bulk_create(objs, batch_size=const.NOTIFICATION_BULK_PUBLISH_CHUNK_SIZE)

    def save_notification_timer(self, timer):
        """
        Will save (create or update) a NotificationCallbackTimer in the
        StorageProvider
        """

        obj = None
        if timer.name:
            # see if it exists
            try:
                obj = SQLNotificationCallbackTimer.objects.get(name=timer.name)
                obj.load_from_data_object(timer)
            except ObjectDoesNotExist:
                pass
        if not obj:
            obj = SQLNotificationCallbackTimer.from_data_object(timer)

        obj.save()
        return obj.to_data_object()

    def get_notification_timer(self, name):
        """
        Will return a single NotificationCallbackTimer
        """
        try:
            obj = SQLNotificationCallbackTimer.objects.get(name=name)
        except ObjectDoesNotExist:
            raise ItemNotFoundError()

        return obj.to_data_object()

    def get_all_active_timers(self, until_time=None, include_executed=False):
        """
        Will return all active timers that are expired as a list

        If until_time is not passed in, then we will use our
        current system time
        """

        objs = SQLNotificationCallbackTimer.objects.filter(
            callback_at__lte=until_time if until_time else datetime.now(pytz.UTC),
            is_active=True
        )

        if not include_executed:
            objs = objs.filter(executed_at__isnull=True)

        return [obj.to_data_object() for obj in objs]

    def get_notification_preference(self, name):
        """
        Will return a single NotificationPreference if exists
        else raises exception ItemNotFoundError
        """
        try:
            obj = SQLNotificationPreference.objects.get(name=name)
        except ObjectDoesNotExist:
            raise ItemNotFoundError()

        return obj.to_data_object()

    def save_notification_preference(self, notification_preference):
        """
        Will save (create or update) a NotificationPreference in the
        StorageProvider
        """
        obj = None
        if notification_preference.name:
            # see if it exists
            try:
                obj = SQLNotificationPreference.objects.get(name=notification_preference.name)
                obj.load_from_data_object(notification_preference)
            except ObjectDoesNotExist:
                pass
        if not obj:
            obj = SQLNotificationPreference.from_data_object(notification_preference)

        obj.save()
        return obj.to_data_object()

    def get_all_notification_preferences(self):
        """
        This returns list of all registered NotificationPreference.
        """
        query = SQLNotificationPreference.objects.all()

        result_set = [item.to_data_object() for item in query]

        return result_set

    def get_user_preference(self, user_id, name):
        """
        Will return a single UserNotificationPreference if exists
        else raises exception ItemNotFoundError
        """
        try:
            obj = SQLUserNotificationPreferences.objects.get(user_id=user_id, preference__name=name)
        except ObjectDoesNotExist:
            raise ItemNotFoundError()

        return obj.to_data_object()

    def set_user_preference(self, user_preference):
        """
        Will save (create or update) a UserNotificationPreference in the
        StorageProvider
        """
        obj = None
        if user_preference.user_id:
            # see if it exists
            try:
                obj = SQLUserNotificationPreferences.objects.get(
                    user_id=user_preference.user_id,
                    preference__name=user_preference.preference.name
                )
                obj.load_from_data_object(user_preference)
            except ObjectDoesNotExist:
                pass
        if not obj:
            obj = SQLUserNotificationPreferences.from_data_object(user_preference)

        obj.save()
        return obj.to_data_object()

    def get_all_user_preferences_for_user(self, user_id):
        """
        This returns list of all UserNotificationPreference.
        """
        query = SQLUserNotificationPreferences.objects.filter(user_id=user_id)

        result_set = [item.to_data_object() for item in query]

        return result_set

    def get_all_user_preferences_with_name(self, name, value, offset=0, size=None):
        """
        Returns a list of UserPreferences objects which match name and value,
        so that we know all users that have the same preference. We need the 'offset'
        and 'size' parameters since this query could potentially be very large
        (imagine a course with 100K students in it) and we'll need the ability to page
        """
        # make sure passed in size is allowed
        # as we don't want to blow up the query too large here
        if size > const.USER_PREFERENCE_MAX_LIST_SIZE:
            raise ValueError('Max limit is {size}'.format(size=size))

        if size is None:
            size = const.USER_PREFERENCE_MAX_LIST_SIZE

        query = SQLUserNotificationPreferences.objects.filter(preference__name=name, value=value)

        query = query[offset:offset + size]

        result_set = [item.to_data_object() for item in query]

        return result_set

    def purge_expired_notifications(self, purge_read_messages_older_than=None, purge_unread_messages_older_than=None):
        """
        Will purge all the unread and read messages that is in the
        db for a period of time.

        purge_read_messages_older_than: will control how old a READ message will remain in the backend

        purge_unread_messages_older_than: will control how old an UNREAD message will remain in the backend

        purge_read_messages_older_than will compare against the "read_at" column

        where as purge_unread_messages_older_than will compare against the "created" column.
        """

        if purge_read_messages_older_than is not None:
            SQLUserNotification.objects.filter(
                read_at__lte=purge_read_messages_older_than).delete()

        if purge_unread_messages_older_than is not None:
            SQLUserNotification.objects.filter(
                created__lte=purge_unread_messages_older_than,
                read_at__isnull=True
            ).delete()

    def get_all_namespaces(self, start_datetime=None, end_datetime=None):
        """
        This will return all unique namespaces that have been used
        """
        result_set = SQLNotificationMessage.objects.all()
        if start_datetime and end_datetime:
            result_set = result_set.filter(created__gte=start_datetime, created__lte=end_datetime)
        result_set = result_set.values_list('namespace', flat=True).order_by('namespace').distinct()

        return result_set
