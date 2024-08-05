"""
Events for email notifications
"""
import datetime

from eventtracking import tracker

from common.djangoapps.track import segment
from openedx.core.djangoapps.notifications.base_notification import COURSE_NOTIFICATION_APPS


EMAIL_DIGEST_SENT = "edx.notifications.email_digest"


def send_user_email_digest_sent_event(user, cadence_type, notifications):
    """
    Sends tracker and segment email for user email digest
    """
    notification_breakdown = {key: 0 for key in COURSE_NOTIFICATION_APPS.keys()}
    for notification in notifications:
        notification_breakdown[notification.app_name] += 1
    event_data = {
        "username": user.username,
        "email": user.email,
        "cadence_type": cadence_type,
        "total_notifications_count": len(notifications),
        "count_breakdown": notification_breakdown,
        "notification_ids": [notification.id for notification in notifications],
        "send_at": str(datetime.datetime.now())
    }
    with tracker.get_tracker().context(EMAIL_DIGEST_SENT, event_data):
        tracker.emit(
            EMAIL_DIGEST_SENT,
            event_data,
        )
        segment.track(
            'None',
            EMAIL_DIGEST_SENT,
            event_data,
        )
