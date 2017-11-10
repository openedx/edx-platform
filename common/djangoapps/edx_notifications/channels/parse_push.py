"""
NotificationChannelProvider to integrate with the Parse mobile push notification services
"""

import logging

from edx_notifications.channels.channel import BaseNotificationChannelProvider
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    publish_timed_notification,
    get_notification_type,
    register_notification_type,
)

from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
)

from edx_notifications.exceptions import (
    ItemNotFoundError,
    ChannelError,
)

from parse_rest.installation import Push
from parse_rest.connection import register
from parse_rest.core import ParseError

# system defined constants that only we should know about
_PARSE_SERVICE_USER_ID = -1000  # 'system' user_ids are < 0
_PARSE_CHANNEL_NAME = 'parse-push'

log = logging.getLogger(__name__)


class ParsePushNotificationChannelProvider(BaseNotificationChannelProvider):
    """
    Implementation of the BaseNotificationChannelProvider abstract interface
    """

    def __init__(self, name=None, display_name=None, display_description=None,
                 link_resolvers=None, application_id=None, rest_api_key=None):
        """
        Initializer
        """

        if not application_id or not rest_api_key:
            raise Exception('Missing application_id or rest_api_key configuration!')

        self.application_id = application_id
        self.rest_api_key = rest_api_key

        super(ParsePushNotificationChannelProvider, self).__init__(
            name=name,
            display_name=display_name,
            display_description=display_description,
            link_resolvers=link_resolvers
        )

    def dispatch_notification_to_user(self, user_id, msg, channel_context=None):
        """
        Send a notification to a user. It is assumed that
        'user_id' and 'msg' are valid and have already passed
        all necessary validations
        """

        # we ONLY can be called with user_id = _PARSE_SERVICE_USER_ID
        if user_id != _PARSE_SERVICE_USER_ID:
            raise ValueError(
                'You must call dispatch_notification_to_user with '
                'only the _PARSE_SERVICE_USER_ID constant!'
            )

        # we expect parse_channel_id in the channel_context
        if not channel_context or 'parse_channel_ids' not in channel_context:
            raise ValueError(
                'You must pass in a non-None channel_context with '
                'the "parse_channel_ids" defined!'
            )

        parse_channel_ids = channel_context.get('parse_channel_ids')

        # parse_channel_ids must be of type list
        if not isinstance(parse_channel_ids, list):
            raise TypeError(
                'The channel context parameter "parse_channel_ids" '
                'must be of python type "list"!'
            )

        # now connect to the Parse service and publish the mobile
        # push notification
        try:
            register(
                self.application_id,
                self.rest_api_key,
            )
            Push.alert(
                data=msg.payload,
                channels=parse_channel_ids,
            )
        except ParseError as error:
            # catch, log, and re-raise
            log.exception(error)

            # re-raise exception
            raise ChannelError(
                'ParsePushNotificationChannelProvider failed to call service. '
                'Error msg = {err_msg}'.format(err_msg=str(error))
            )

    def bulk_dispatch_notification(self, user_ids, msg, exclude_user_ids=None, channel_context=None):
        """
        Perform a bulk dispatch of the notification message to
        all user_ids that will be enumerated over in user_ids.

        In reality, for Parse push notifications, since we are really only
        publishing a notification to a system Service id, there should only
        be one element in the user_ids array
        """

        cnt = 0
        for user_id in user_ids:
            if not exclude_user_ids or user_id not in exclude_user_ids:
                self.dispatch_notification_to_user(user_id, msg, channel_context=channel_context)
                cnt += 1

        return cnt

    def resolve_msg_link(self, msg, link_name, params, channel_context=None):
        """
        Generates the appropriate link given a msg, a link_name, and params
        """
        # Click through links do not apply for mobile push notifications
        return None

    @classmethod
    def publish_notification(cls, namespace, msg_type_name, payload, parse_channel_ids, send_at=None, timer_name=None):
        """
        Helper class method to hide some of the inner workings of this channel
        This will work with immediate or timer based publishing.

        'namespace' is an instance of NotificationMessage

        'msg_type' is the type name of the NotificationMessage

        'payload' is the raw data dictionary to send over the mobile clients

        'parse_channel_ids' is a list of Parse channel_ids, which are subscription lists,
        not to be confused with edx-notification's NotificationChannels - an unfortunate
        semantic collision.

        'send_at' is a datetime when this notification should be sent. Note that firing of notifications
        is approximate, so it will not fire BEFORE send_at, but there might be a lag, depending
        on how frequent timer polling is configured in a runtime instance.

        'timer_name' can be used in conjunction with 'send_at'. This is to allow for a fixed
        timer identifier in case the timed notification needs to be updated (or deleted)
        """

        try:
            msg_type = get_notification_type(msg_type_name)
        except ItemNotFoundError:
            msg_type = NotificationType(
                name=msg_type_name,
                renderer='edx_notifications.renderers.basic.JsonRenderer'
            )
            register_notification_type(msg_type)

        msg = NotificationMessage(
            namespace=namespace,
            msg_type=msg_type,
            payload=payload
        )

        if not send_at:
            # send immediately
            publish_notification_to_user(
                user_id=_PARSE_SERVICE_USER_ID,
                msg=msg,
                # we want to make sure we always call this channel provider
                preferred_channel=_PARSE_CHANNEL_NAME,
                channel_context={
                    # tunnel through the parse_channel_id through the
                    # channel context
                    'parse_channel_ids': parse_channel_ids,
                }
            )
        else:
            # time-based sending, use a TimedNotification
            publish_timed_notification(
                msg=msg,
                send_at=send_at,
                scope_name='user',
                scope_context={
                    'user_id': _PARSE_SERVICE_USER_ID
                },
                timer_name=timer_name,
                timer_context={
                    # we want to make sure we always call this channel provider
                    'preferred_channel': _PARSE_CHANNEL_NAME,
                    'channel_context': {
                        # tunnel through the parse_channel_id through
                        # through the channel context
                        'parse_channel_ids': parse_channel_ids,
                    }
                }
            )
