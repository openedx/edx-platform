"""
Celery tasks used by badging
"""
from celery.task import task
from django.conf import settings
from django.urls import reverse

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email

from .constants import COURSE_ID_KEY, MY_BADGES_URL_NAME


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_user_badge_notify(user, course_id, badge_name):
    """
    Send email and generate a notification to user, when he earns new badge.
    """
    from .helpers.notifications import send_user_badge_notification

    my_badge_url = u'{host}{path}'.format(
        host=settings.LMS_ROOT_URL,
        path=reverse(MY_BADGES_URL_NAME, kwargs={COURSE_ID_KEY: course_id})
    )
    context = {
        'emailId': HubSpotClient.USER_NEW_BADGE_EMAIL,
        'message': {
            'to': user.email
        },
        'customProperties': {
            'my_badge_url': my_badge_url,
        }
    }
    task_send_hubspot_email.delay(context)

    send_user_badge_notification(user, my_badge_url, badge_name)
