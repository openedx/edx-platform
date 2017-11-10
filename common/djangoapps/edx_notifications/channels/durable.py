"""
Implements a durable notification channel which will be a base class
that saves Notifications to a database for later
retrieval
"""

import logging

from edx_notifications import const
from edx_notifications.channels.channel import BaseNotificationChannelProvider
from edx_notifications.channels.link_resolvers import MsgTypeToUrlResolverMixin

from edx_notifications.stores.store import notification_store

from edx_notifications.data import (
    UserNotification,
)

log = logging.getLogger(__name__)


class BaseDurableNotificationChannel(MsgTypeToUrlResolverMixin, BaseNotificationChannelProvider):
    """
    A durable notification channel will save messages to
    the database. This can be subclassed by any specialized
    Channel provider if it was to provide custom behavior (but still
    has the characteristic of using a durable stoage backend)
    """

    def dispatch_notification_to_user(self, user_id, msg, channel_context=None):
        """
        Send a notification to a user, which - in a durable Notification -
        is simply store it in the database, and - soon in the future -
        raise some signal to a waiting client that a message is available
        """

        store = notification_store()

        # get a msg (cloned from original) with resolved links
        msg = self._get_linked_resolved_msg(msg)

        # persist the message in our Store Provide
        _msg = store.save_notification_message(msg)

        # create a new UserNotification and point to the new message
        # this new mapping will have the message in an unread state
        # NOTE: We need to set this up after msg is saved otherwise
        # we won't have it's primary key (id)
        user_msg = UserNotification(
            user_id=user_id,
            msg=_msg
        )

        _user_msg = store.save_user_notification(user_msg)

        #
        # When we support in-broswer push notifications
        # such as Comet/WebSockets, this is where we should
        # signal the client to come fetch the
        # notification that has just been dispatched
        #

        #
        # Here is where we will tie into the Analytics pipeline
        #

        return _user_msg

    def bulk_dispatch_notification(self, user_ids, msg, exclude_user_ids=None, channel_context=None):
        """
        Perform a bulk dispatch of the notification message to
        all user_ids that will be enumerated over in user_ids.

        NOTE: We will chunk together up to NOTIFICATION_BULK_PUBLISH_CHUNK_SIZE

        user_ids should be a list, a generator function, or a
        django.db.models.query.ValuesQuerySet/ValuesListQuerySet
        when directly feeding in a Django ORM queryset, where we select just the id column of the user
        """

        store = notification_store()

        # get a msg (cloned from original) with resolved links
        msg = self._get_linked_resolved_msg(msg)

        # persist the message in our Store Provide
        _msg = store.save_notification_message(msg)

        user_msgs = []

        exclude_user_ids = exclude_user_ids if exclude_user_ids else []

        cnt = 0
        total = 0

        # enumerate through the list of user_ids and chunk them
        # up. Be sure not to include any user_id in the exclude list
        for user_id in user_ids:
            if user_id not in exclude_user_ids:
                user_msgs.append(
                    UserNotification(
                        user_id=user_id,
                        msg=_msg
                    )
                )
                cnt = cnt + 1
                total = total + 1
                if cnt == const.NOTIFICATION_BULK_PUBLISH_CHUNK_SIZE:
                    store.bulk_create_user_notification(user_msgs)
                    user_msgs = []
                    cnt = 0

        if user_msgs:
            store.bulk_create_user_notification(user_msgs)

        return total
