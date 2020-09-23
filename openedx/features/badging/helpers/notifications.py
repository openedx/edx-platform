"""
Helper methods for badging notifications
"""
from django.template.loader import render_to_string
from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import get_notification_type, publish_notification_to_user

from openedx.features.badging.constants import EARNED_BADGE_NOTIFICATION_TYPE


def send_user_badge_notification(user, my_badge_url, badge_name):
    """
    Send user new badge notification
    :param user: User receiving the Notification
    :param my_badge_url: Redirect url to my_badge view on notification click
    :param badge_name: Newly earned badge
    """
    context = {
        'badge_name': badge_name
    }

    body_short = render_to_string('philu_notifications/templates/user_badge_earned.html', context)

    message = NotificationMessage(
        msg_type=get_notification_type(EARNED_BADGE_NOTIFICATION_TYPE),
        payload={
            'from_user': user.username,
            'path': my_badge_url,
            'bodyShort': body_short,
        }
    )

    publish_notification_to_user(user.id, message)
