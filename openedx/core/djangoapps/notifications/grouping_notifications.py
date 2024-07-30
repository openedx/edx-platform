"""
Utils for grouping notifications
"""
import datetime

from pytz import utc
from openedx.core.djangoapps.notifications.models import Notification


def get_notification_type_grouping_function(notification_type):
    """
    Returns a method that groups notification of same notification type
    If method doesn't exist, it returns None
    """
    try:
        return globals()[f"group_{notification_type}_notification"]
    except KeyError:
        return None


def get_user_existing_notifications(user_ids, notification_type, group_by_id, course_id):
    """
    Returns user last groupable notification
    """
    notifications = Notification.objects.filter(
        user__in=user_ids, notification_type=notification_type, group_by_id=group_by_id,
        course_id=course_id
    )
    notifications_mapping = {user_id: [] for user_id in user_ids}
    for notification in notifications:
        notifications_mapping[notification.user_id].append(notification)

    for user_id, notifications in notifications_mapping.items():
        notifications.sort(key=lambda elem: elem.created)
        notifications_mapping[user_id] = notifications[0] if notifications else None
    return notifications_mapping


def group_user_notifications(new_notification, old_notification):
    """
    Groups user notification based on notification type and group_id
    Params:
        new_notification: [Notification] (Donot used object that has already been saved to DB)
        existing_notifications: List[Notification]. Latest created notification will be updated to grouped
    """
    notification_type = new_notification.notification_type
    func = get_notification_type_grouping_function(notification_type)
    func(new_notification, old_notification)
    old_notification.content_context['grouped'] = True
    old_notification.web = old_notification.web or new_notification.web
    old_notification.email = old_notification.email or new_notification.email
    old_notification.last_read = None
    old_notification.last_seen = None
    old_notification.created = utc.localize(datetime.datetime.now())
    old_notification.save()


def group_new_comment_notification(new_notification, old_notification):
    """
    Groups new_comment notification
    """
    context = old_notification.content_context
    user_key = 'replier_name'
    group_key = f'{user_key}_grouped'
    if not context.get('grouped'):
        context['user_key'] = user_key
        context['group_key'] = group_key
        context[group_key] = [context[user_key]]
        context['grouped_count'] = 1
        context['grouped'] = True
    context[group_key].append(new_notification.content_context['replier_name'])
    context['grouped_count'] += 1
