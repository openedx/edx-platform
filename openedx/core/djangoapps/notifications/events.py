""" Events for notification app. """

from eventtracking import tracker

from common.djangoapps.track import contexts, segment

NOTIFICATION_PREFERENCES_VIEWED = 'edx.notifications.preferences.viewed'
NOTIFICATION_GENERATED = 'edx.notifications.generated'
NOTIFICATION_READ = 'edx.notifications.read'
NOTIFICATION_APP_ALL_READ = 'edx.notifications.app_all_read'
NOTIFICATION_PREFERENCES_UPDATED = 'edx.notifications.preferences.updated'
NOTIFICATION_TRAY_OPENED = 'edx.notifications.tray_opened'
NOTIFICATION_PREFERENCE_UNSUBSCRIBE = 'edx.notifications.preferences.one_click_unsubscribe'


def get_user_forums_roles(user, course_id):
    """
    Get the user's roles in the course forums.
    """
    if course_id:
        return list(user.roles.filter(course_id=course_id).values_list('name', flat=True))
    return []


def get_user_course_roles(user, course_id):
    """
    Get the user's roles in the course.
    """
    if course_id:
        return list(user.courseaccessrole_set.filter(course_id=course_id).values_list('role', flat=True))
    return []


def notification_event_context(user, course_id, notification):
    return {
        'user_id': str(user.id),
        'course_id': str(course_id),
        'notification_type': notification.notification_type,
        'notification_app': notification.app_name,
        'notification_metadata': {
            'notification_id': notification.id,
            'notification_content': notification.content,
        },
        'user_forum_roles': get_user_forums_roles(user, course_id),
        'user_course_roles': get_user_course_roles(user, course_id),
    }


def notification_preferences_viewed_event(request, course_id):
    """
    Emit an event when a user views their notification preferences.
    """
    context = contexts.course_context_from_course_id(course_id)
    with tracker.get_tracker().context(NOTIFICATION_PREFERENCES_VIEWED, context):
        tracker.emit(
            NOTIFICATION_PREFERENCES_VIEWED,
            {
                'user_id': str(request.user.id),
                'course_id': str(course_id),
                'user_forum_roles': get_user_forums_roles(request.user, course_id),
                'user_course_roles': get_user_course_roles(request.user, course_id),
            }
        )


def notification_generated_event(user_ids, app_name, notification_type, course_key,
                                 content_url, content, sender_id=None):
    """
    Emit an event when a notification is generated.
    """
    context = contexts.course_context_from_course_id(course_key)
    context['user_id'] = 'None'
    recipients_count = len(user_ids)
    event_data = {
        'recipients_id': user_ids[:100],
        'recipients_count': recipients_count,
        'recipients_truncated': recipients_count > 100,
        'course_id': str(course_key),
        'notification_type': notification_type,
        'notification_app': app_name,
        'content_url': content_url,
        'notification_content': content,
        'sender_id': sender_id,
    }
    with tracker.get_tracker().context(NOTIFICATION_GENERATED, context):
        tracker.emit(
            NOTIFICATION_GENERATED,
            event_data,
        )
        segment.track(
            'None',
            NOTIFICATION_GENERATED,
            event_data,
        )


def notification_read_event(user, notification, first_read=False):
    """
    Emit an event when a notification app is marked read for a user.
    """
    context = contexts.course_context_from_course_id(notification.course_id)
    event_data = notification_event_context(user, notification.course_id, notification)
    event_data['first_read'] = first_read
    with tracker.get_tracker().context(NOTIFICATION_READ, context):
        tracker.emit(
            NOTIFICATION_READ,
            event_data,
        )


def notifications_app_all_read_event(user, app_name):
    """
    Emit an event when a notification is read.
    """
    tracker.emit(
        NOTIFICATION_APP_ALL_READ,
        {
            'user_id': str(user.id),
            'notification_app': app_name,
        }
    )


def notification_preference_update_event(user, course_id, updated_preference):
    """
    Emit an event when a notification preference is updated.
    """
    context = contexts.course_context_from_course_id(course_id)
    with tracker.get_tracker().context(NOTIFICATION_PREFERENCES_UPDATED, context):
        value = updated_preference.get('value', '')
        if updated_preference.get('notification_channel', '') == 'email_cadence':
            value = updated_preference.get('email_cadence', '')
        tracker.emit(
            NOTIFICATION_PREFERENCES_UPDATED,
            {
                'user_id': str(user.id),
                'course_id': str(course_id),
                'user_forum_roles': get_user_forums_roles(user, course_id),
                'user_course_roles': get_user_course_roles(user, course_id),
                'notification_app': updated_preference.get('notification_app', ''),
                'notification_type': updated_preference.get('notification_type', ''),
                'notification_channel': updated_preference.get('notification_channel', ''),
                'value': value
            }
        )


def notification_tray_opened_event(user, unseen_notifications_count):
    """
    Emit an event when a notification tray is opened.
    """
    tracker.emit(
        NOTIFICATION_TRAY_OPENED,
        {
            'user_id': user.id,
            'unseen_notifications_count': unseen_notifications_count,
        }
    )


def notification_preference_unsubscribe_event(user):
    """
    Emits an event when user clicks on one-click-unsubscribe url
    """
    event_data = {
        'user_id': user.id,
        'username': user.username,
        'event_type': 'email_digest_unsubscribe'
    }
    tracker.emit(NOTIFICATION_PREFERENCE_UNSUBSCRIBE, event_data)
    segment.track(user.id, NOTIFICATION_PREFERENCE_UNSUBSCRIBE, event_data)
