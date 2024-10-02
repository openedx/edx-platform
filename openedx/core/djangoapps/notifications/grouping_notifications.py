"""
Notification grouping utilities for notifications
"""
import datetime
from typing import Dict, Type, Union

from pytz import utc

from abc import ABC, abstractmethod

from openedx.core.djangoapps.notifications.models import Notification


class BaseNotificationGrouper(ABC):
    """
    Base class for notification groupers.
    """

    @abstractmethod
    def group(self, new_notification, old_notification):
        pass


class NotificationRegistry:
    """
    Registry for notification groupers.
    """
    _groupers: Dict[str, Type[BaseNotificationGrouper]] = {}

    @classmethod
    def register(cls, notification_type: str):
        """
        Registers a notification grouper for the given notification type.
        Args
            notification_type: The type of notification for which to register the grouper.

        Returns:
            A decorator that registers the grouper class for the given notification type.
        """

        def decorator(grouper_class: Type[BaseNotificationGrouper]) -> Type[BaseNotificationGrouper]:
            """
            Registers the grouper class for the given notification type.
            """
            cls._groupers[notification_type] = grouper_class
            return grouper_class

        return decorator

    @classmethod
    def get_grouper(cls, notification_type: str) -> Union[BaseNotificationGrouper, None]:
        """Retrieves the appropriate notification grouper based on the given notification type.

        Args:
            notification_type: The type of notification for which to retrieve the grouper.

        Returns:
            The corresponding BaseNotificationGrouper instance or None if no grouper is found.
        """
        grouper_class = cls._groupers.get(notification_type)
        if not grouper_class:
            return None
        return grouper_class()


@NotificationRegistry.register('new_comment')
class NewCommentGrouper(BaseNotificationGrouper):
    """
    Groups new comment notifications based on the replier name.
    """

    def group(self, new_notification, old_notification):
        """
        Groups new comment notifications based on the replier name.
        """
        context = old_notification.content_context.copy()
        if not context.get('grouped'):
            context['replier_name_list'] = [context['replier_name']]
            context['grouped_count'] = 1
            context['grouped'] = True
        context['replier_name_list'].append(new_notification.content_context['replier_name'])
        context['grouped_count'] += 1
        return context


def group_user_notifications(new_notification: Notification, old_notification: Notification):
    """
    Groups user notification based on notification type and group_id
    """
    notification_type = new_notification.notification_type
    grouper_class = NotificationRegistry.get_grouper(notification_type)

    if grouper_class:
        old_notification.content_context = grouper_class.group(new_notification, old_notification)
        old_notification.content_context['grouped'] = True
        old_notification.web = old_notification.web or new_notification.web
        old_notification.email = old_notification.email or new_notification.email
        old_notification.last_read = None
        old_notification.last_seen = None
        old_notification.created = utc.localize(datetime.datetime.now())
        old_notification.save()


def get_user_existing_notifications(user_ids, notification_type, group_by_id, course_id):
    """
    Returns user last group able notification
    """
    notifications = Notification.objects.filter(
        user__in=user_ids,
        notification_type=notification_type,
        group_by_id=group_by_id,
        course_id=course_id
    )
    notifications_mapping = {user_id: [] for user_id in user_ids}
    for notification in notifications:
        notifications_mapping[notification.user_id].append(notification)

    for user_id, notifications in notifications_mapping.items():
        notifications.sort(key=lambda elem: elem.created)
        notifications_mapping[user_id] = notifications[0] if notifications else None
    return notifications_mapping
