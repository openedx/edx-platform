""" Events for notification app. """

from eventtracking import tracker

from common.djangoapps.track import contexts, segment

NOTIFICATION_PREFERENCES_VIEWED = 'edx.notifications.preferences.viewed'
NOTIFICATION_GENERATED = 'edx.notifications.generated'
NOTIFICATION_READ = 'edx.notifications.read'
NOTIFICATION_APP_ALL_READ = 'edx.notifications.app_all_read'
NOTIFICATION_PREFERENCES_UPDATED = 'edx.notifications.preferences.updated'
NOTIFICATION_TRAY_OPENED = 'edx.notifications.tray_opened'


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


def notification_generated_event(user_ids, app_name, notification_type, course_key):
    """
    Emit an event when a notification is generated.
    """
    context = contexts.course_context_from_course_id(course_key)
    event_data = {
        'recipients_id': user_ids,
        'course_id': str(course_key),
        'notification_type': notification_type,
        'notification_app': app_name,
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


def notification_read_event(user, notification):
    """
    Emit an event when a notification app is marked read for a user.
    """
    context = contexts.course_context_from_course_id(notification.course_id)
    with tracker.get_tracker().context(NOTIFICATION_READ, context):
        tracker.emit(
            NOTIFICATION_READ,
            notification_event_context(user, notification.course_id, notification)
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
                'value': updated_preference.get('value', ''),
            }
        )


def notification_tray_opened_event(user):
    """
    Emit an event when a notification tray is opened.
    """
    tracker.emit(
        NOTIFICATION_TRAY_OPENED,
        {
            'user_id': user.id,
        }
    )
