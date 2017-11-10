"""
Any internal Timer callbacks
"""

import abc
import logging

from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    bulk_publish_notification_to_users,
    purge_expired_notifications)
from edx_notifications.scopes import resolve_user_scope
from edx_notifications.stores.store import notification_store
from edx_notifications.exceptions import ItemNotFoundError

log = logging.getLogger(__name__)


class NotificationCallbackTimerHandler(object):
    """
    Interface for timer callbacks
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def notification_timer_callback(self, timer):
        """
        This must be implemented by any class that inherits this interface.

        Implementations MUST return a dict with the following structure
            {
                'num_dispatched': xxx,
                'errors': ['','',...],
                'reschedule_in_mins': xxx,
            }

        if the handler wishes to reschedule the same timer, it
        should return an integer value representing the number of minutes
        when it should be re-run.

        NOTE: The system will put a minimum number of minutes on any
        rescheduling of calls. This is settable via configuration.
        """
        msg = (
            'Must define "handle_notification_callback" in class="{class_name}"!'
        ).format(class_name=self.__class__.__name__)

        raise NotImplementedError(msg)


class NotificationDispatchMessageCallback(NotificationCallbackTimerHandler):
    """
    This is called by the NotificationTimer when there is a
    timed notification that needs to be dispatched

    The timer context must have this schema:

        {
            'msg_id': xxxx,
            'distribution_scope': {
                'name': <name of the scope: user, course_group, or course_enrollments>,
                'scope_context': <any information that gets passed into any scope resolvers, see below>
            }
        }

        scope_context:
            if scope='user': then {'user_id': xxxx }
            if scope='course_group' then {'course_id': xxxx, 'group_id': xxxxx}
            if scope='course_enrollments' then {'course_id'}
    """

    def notification_timer_callback(self, timer):
        num_dispatched = 0
        err_msgs = []

        try:
            context = timer.context

            # make sure we have all information we need
            # in our various contexts
            check_keys = (
                'distribution_scope' in context and
                'msg_id' in context and
                'scope_name' in context['distribution_scope'] and
                'scope_context' in context['distribution_scope']
            )
            if not check_keys:
                err_msg = (
                    'Malformed timer "{name}" context! Expected a keys of '
                    '"msg_id", "distribution_scope.name", and '
                    '"distribution_scope.scope_context" in '
                    'timer context but could not find it in {context}.'
                ).format(name=timer.name, context=context)
                raise KeyError(err_msg)

            msg_id = int(context['msg_id'])
            scope_name = context['distribution_scope']['scope_name']
            scope_context = context['distribution_scope']['scope_context']

            log_msg = (
                'Firing timed Notification to scope name "{scope_name}" and scope '
                'context {scope_context} with message_id: {msg_id}'
            ).format(scope_name=scope_name, scope_context=scope_context, msg_id=msg_id)
            log.info(log_msg)

            channel_context = context.get('channel_context')
            preferred_channel = context.get('preferred_channel')

            try:
                notification_msg = notification_store().get_notification_message_by_id(msg_id)
            except ItemNotFoundError:
                err_msg = (
                    'Could not find msg_id {msg_id} associated '
                    'with timer "{name}". Message was not sent!'
                ).format(msg_id=msg_id, name=timer.name)

            if scope_name == 'user':
                num_dispatched = _send_to_single_user(
                    notification_msg,
                    scope_context,
                    preferred_channel=preferred_channel,
                    channel_context=channel_context
                )
                num_dispatched = 1
            else:
                num_dispatched = _send_to_scoped_users(
                    notification_msg,
                    scope_name,
                    scope_context,
                    preferred_channel=preferred_channel,
                    channel_context=channel_context
                )

        except Exception, ex:  # pylint: disable=broad-except
            log.exception(ex)
            err_msgs.append(str(ex))

        result = {
            'num_dispatched': num_dispatched,
            'errors': err_msgs,
            'reschedule_in_mins': None,
        }

        return result


def _send_to_single_user(msg, scope_context, preferred_channel=None, channel_context=None):
    """
    Helper method to send to just a single user
    """

    # make sure the user_id was passed in
    if 'user_id' not in scope_context:
        err_msg = (
            'Could not find "user_id" in scope_context {context}'
        ).format(context=scope_context)

        raise KeyError(err_msg)

    user_id = int(scope_context['user_id'])

    # finally publish the notification
    publish_notification_to_user(
        user_id,
        msg,
        preferred_channel=preferred_channel,
        channel_context=channel_context
    )

    return 1


def _send_to_scoped_users(msg, scope_name, scope_context, preferred_channel=None, channel_context=None):
    """
    Helper method to send to a scoped set of users.
    scope_context contains all of the information
    that can be passed into a NotificationScopeResolver
    """

    # user_ids can be a list, a generator function, or a ValuesQuerySet/ValuesListQuerySet (Django ORM)
    user_ids = resolve_user_scope(scope_name, scope_context)

    if not user_ids:
        err_msg = (
            'Could not resolve distribution scope "{name}" with context {context}! '
            'Message id "{_id}" was not sent!'
        ).format(name=scope_name, context=scope_context, _id=msg.id)

        raise Exception(err_msg)

    # optional parameter to exclude certain
    # ids
    exclude_list = scope_context.get('exclude_user_ids')

    num_dispatched = bulk_publish_notification_to_users(
        user_ids,
        msg,
        exclude_user_ids=exclude_list,
        preferred_channel=preferred_channel,
        channel_context=channel_context
    )

    return num_dispatched


class PurgeNotificationsCallbackHandler(NotificationCallbackTimerHandler):
    """
        This is the callback class called by the NotificationTimer for purging old notifications.
        It will be rescheduled daily and will purge the old notifications by calling the StoreProvider
        method

        The return dictionary must contain the key 'reschedule_in_mins' with
        the value timer.periodicity_min in order to re-arm the callback to
        trigger again after the specified interval.
    """

    def notification_timer_callback(self, timer):
        purge_expired_notifications()

        # Reschedule the timer to run again the next day.
        result = {
            'errors': [],
            'reschedule_in_mins': timer.periodicity_min,
        }
        return result
