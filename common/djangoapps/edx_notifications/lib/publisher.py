"""
All in-proc API endpoints for acting as a Notification Publisher

IMPORTANT: All methods exposed here will also be exposed in as a
xBlock runtime service named 'notifications'. Be aware that adding
any new methods here will also be exposed to xBlocks!!!!
"""

import logging
import types
import datetime
import pytz
import copy
from contracts import contract

from django.db.models.query import ValuesQuerySet, ValuesListQuerySet

from edx_notifications.channels.channel import get_notification_channel
from edx_notifications import const
from edx_notifications.stores.store import notification_store
from edx_notifications.exceptions import ItemNotFoundError

from edx_notifications.data import (
    NotificationType,
    NotificationMessage,
    NotificationCallbackTimer,
)

from edx_notifications.renderers.renderer import (
    register_renderer
)
from edx_notifications.scopes import resolve_user_scope, has_user_scope_resolver

log = logging.getLogger(__name__)


@contract(msg_type=NotificationType)
def register_notification_type(msg_type):
    """
    Registers a new notification type
    """

    log.info('Registering NotificationType: {msg_type}'.format(msg_type=str(msg_type)))

    # do validation
    msg_type.validate()

    notification_store().save_notification_type(msg_type)

    # also register the Renderer associated with this
    # type, note that the multiple msg types can have
    # the same renderer, but only one entry will
    # get placed in the registry
    register_renderer(msg_type.renderer)


@contract(type_name=basestring)
def get_notification_type(type_name):
    """
    Returns the NotificationType registered by type_name
    """

    return notification_store().get_notification_type(type_name)


def get_all_notification_types():
    """
    Returns all know Notification types
    """

    return notification_store().get_all_notification_types()


@contract(user_id='int', msg=NotificationMessage)
def publish_notification_to_user(user_id, msg, preferred_channel=None, channel_context=None):
    """
    This top level API method will publish a notification
    to a user.

    Ultimately this method will look up the user's preference
    to which NotificationChannel to distribute this over.

    ARGS:
        - user_id: An unconstrained identifier to some user identity
        - msg: A NotificationMessage

    RETURNS:
        A new instance of UserNotification that includes any auto-generated
        fields
    """

    log_msg = (
        'Publishing Notification to user_id {user_id} with message: {msg}'
    ).format(user_id=user_id, msg=msg)
    log.info(log_msg)

    # validate the msg, this will raise a ValidationError if there
    # is something malformatted or missing in the NotificationMessage
    msg.validate()

    # get the notification channel associated
    # for this message type as well as this user
    # as users will be able to choose how to
    # receive their notifications per type.
    #
    # This call will never return None, if there is
    # a problem, it will throw an exception
    channel = get_notification_channel(user_id, msg.msg_type, preferred_channel=preferred_channel)

    # Get the proper message - aka payload - for the given channel
    _msg = msg.get_message_for_channel(channel.name)

    user_msg = channel.dispatch_notification_to_user(user_id, _msg, channel_context=channel_context)

    return user_msg


@contract(msg=NotificationMessage)
def bulk_publish_notification_to_users(user_ids, msg, exclude_user_ids=None,
                                       preferred_channel=None, channel_context=None):
    """
    This top level API method will publish a notification
    to a group (potentially large). We have a distinct entry
    point to consider any optimizations that might be possible
    when doing bulk operations

    Ultimately this method will look up the user's preference
    to which NotificationChannel to distribute this over.

    ARGS:
        - user_ids: an iterator that we can enumerate over, say a list or a generator or a ORM resultset
        - msg: A NotificationMessage

    IMPORTANT: If caller wishes to send in a resutset from a Django ORM query, you must
    only select the 'id' column and flatten the results. For example, to send a notification
    to everyone in the Users table, do:

        num_sent = bulk_publish_notification_to_users(
            User.objects.values_list('id', flat=True).all(),
            msg
        )

    """

    log.info('Publishing bulk Notification with message: {msg}'.format(msg=msg))

    # validate the msg, this will raise a ValidationError if there
    # is something malformatted or missing in the NotificationMessage
    msg.validate()

    if (not isinstance(user_ids, list) and
            not isinstance(user_ids, types.GeneratorType) and
            not isinstance(user_ids, ValuesListQuerySet) and
            not isinstance(user_ids, ValuesQuerySet)):

        err_msg = (
            'bulk_publish_notification_to_users() can only be called with a user_ids argument '
            'of type list, GeneratorType, or ValuesQuerySet/ValuesListQuerySet. Type {arg_type} was passed in!'
            .format(arg_type=type(user_ids))
        )
        raise TypeError(err_msg)

    # validate the msg, this will raise a ValidationError if there
    # is something malformatted or missing in the NotificationMessage
    msg.validate()

    # get the system defined msg_type -> channel mapping
    # note, when we enable user preferences, we will
    # have to change this
    channel = get_notification_channel(None, msg.msg_type, preferred_channel=preferred_channel)

    # Get the proper message - aka payload - for the given channel
    _msg = msg.get_message_for_channel(channel.name)

    num_sent = channel.bulk_dispatch_notification(
        user_ids,
        _msg,
        exclude_user_ids=exclude_user_ids,
        channel_context=channel_context
    )

    return num_sent


@contract(msg=NotificationMessage)
def bulk_publish_notification_to_scope(scope_name, scope_context, msg, exclude_user_ids=None,
                                       preferred_channel=None, channel_context=None):
    """
    This top level API method will publish a notification
    to a UserScope (potentially large). Basically this is a convenience method
    which simple resolves the scope and then called into
    bulk_publish_notifications_to_scope()

    IMPORTANT: In general one will want to call into this method behind a
    Celery task

    For built in Scope Resolvers ('course_group', 'course_enrollments')

        scope_context:
            if scope='course_group' then context = {'course_id': xxxx, 'group_id': xxxxx}
            if scope='course_enrollments' then context = {'course_id'}

    """
    log_msg = (
        'Publishing scoped Notification to scope name "{scope_name}" and scope '
        'context {scope_context} with message: {msg}'
    ).format(scope_name=scope_name, scope_context=scope_context, msg=msg)
    log.info(log_msg)

    user_ids = resolve_user_scope(scope_name, scope_context)

    if not user_ids:
        return 0

    return bulk_publish_notification_to_users(
        user_ids,
        msg,
        exclude_user_ids,
        preferred_channel=preferred_channel,
        channel_context=channel_context
    )


@contract(msg=NotificationMessage, send_at=datetime.datetime, scope_name=basestring, scope_context=dict)
def publish_timed_notification(msg, send_at, scope_name, scope_context, timer_name=None,
                               ignore_if_past_due=False, timer_context=None):  # pylint: disable=too-many-arguments
    """
    Registers a new notification message to be dispatched
    at a particular time.

    IMPORTANT: There can only be one timer associated with
    a notification message. If it is called more than once on the
    same msg_id, then the existing one is updated.

    ARGS:
        send_at: datetime when the message should be sent
        msg: An instance of a NotificationMessage
        distribution_scope: enum of three values: 'user', 'course_group', 'course_enrollments'
               which describe the distribution scope of the message
        scope_context:
            if scope='user': then {'user_id': xxxx }
            if scope='course_group' then {'course_id': xxxx, 'group_id': xxxxx}
            if scope='course_enrollments' then {'course_id'}

        timer_name: if we know the name of the timer we want to use rather than auto-generating it.
                    use caution not to mess with other code's timers!!!
        ignore_if_past_due: If the notification should not be put into the timers, if the send date
                    is in the past

    RETURNS: instance of NotificationCallbackTimer
    """

    now = datetime.datetime.now(pytz.UTC)
    if now > send_at and ignore_if_past_due:
        log.info('Timed Notification is past due and the caller said to ignore_if_past_due. Dropping notification...')
        if timer_name:
            # If timer is named and it is past due, it is possibly being updated
            # so, then we should remove any previously stored
            # timed notification
            cancel_timed_notification(timer_name, exception_on_not_found=False)
        return

    # make sure we can resolve the scope_name
    if not has_user_scope_resolver(scope_name):
        err_msg = (
            'There is no registered scope resolver for scope_name "{name}"'
        ).format(name=scope_name)
        raise ValueError(err_msg)

    store = notification_store()

    # make sure we put the delivery timestamp on the message as well
    msg.deliver_no_earlier_than = send_at
    saved_msg = store.save_notification_message(msg)

    _timer_name = timer_name if timer_name else 'notification-dispatch-timer-{_id}'.format(_id=saved_msg.id)

    log_msg = (
        'Publishing timed Notification named "{timer_name}" to scope name "{scope_name}" and scope '
        'context {scope_context} to be sent at "{send_at} with message: {msg}'
    ).format(timer_name=_timer_name, scope_name=scope_name, scope_context=scope_context, send_at=send_at, msg=msg)
    log.info(log_msg)

    _timer_context = copy.deepcopy(timer_context) if timer_context else {}

    # add in the context that is predefined
    _timer_context.update({
        'msg_id': saved_msg.id,
        'distribution_scope': {
            'scope_name': scope_name,
            'scope_context': scope_context,
        }
    })

    timer = NotificationCallbackTimer(
        name=_timer_name,
        callback_at=send_at,
        class_name='edx_notifications.callbacks.NotificationDispatchMessageCallback',
        is_active=True,
        context=_timer_context
    )

    saved_timer = store.save_notification_timer(timer)

    return saved_timer


@contract(timer_name=basestring)
def cancel_timed_notification(timer_name, exception_on_not_found=True):
    """
    Cancels a previously published timed notification
    """

    log_msg = (
        'Cancelling timed Notification named "{timer_name}"'
    ).format(timer_name=timer_name)
    log.info(log_msg)

    store = notification_store()
    try:
        timer = store.get_notification_timer(timer_name)
        timer.is_active = False  # simply make is_active=False
        store.save_notification_timer(timer)
    except ItemNotFoundError:
        if not exception_on_not_found:
            return

        err_msg = (
            'Tried to call cancel_timed_notification for timer_name "{name}" '
            'but it does not exist. Skipping...'
        ).format(name=timer_name)
        log.error(err_msg)


def purge_expired_notifications():
    """
    This method reads from the configuration how long (in days) old notifications (read and unread separately)
    can remain in the system before being purged. Lack of configuration (or None) means "don't purge ever"
    and calls into the store provider's purge_expired_notifications() method.
    """

    store = notification_store()
    now = datetime.datetime.now(pytz.UTC)

    purge_read_older_than = None
    if const.NOTIFICATION_PURGE_READ_OLDER_THAN_DAYS:
        purge_read_older_than = now - datetime.timedelta(days=const.NOTIFICATION_PURGE_READ_OLDER_THAN_DAYS)

    purge_unread_older_than = None
    if const.NOTIFICATION_PURGE_UNREAD_OLDER_THAN_DAYS:
        purge_unread_older_than = now - datetime.timedelta(days=const.NOTIFICATION_PURGE_UNREAD_OLDER_THAN_DAYS)

    store.purge_expired_notifications(
        purge_read_messages_older_than=purge_read_older_than,
        purge_unread_messages_older_than=purge_unread_older_than
    )
