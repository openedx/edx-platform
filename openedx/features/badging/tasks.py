from celery.task import task
from django.conf import settings
from django.urls import reverse

from common.lib.mandrill_client.client import MandrillClient

from .constants import COURSE_ID_KEY, MY_BADGES_URL_NAME


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_user_badge_email(user_email, course_id):
    """Send email to user, when he earns new badge."""
    my_badge_url = u'{host}{path}'.format(
        host=settings.LMS_ROOT_URL,
        path=reverse(MY_BADGES_URL_NAME, kwargs={COURSE_ID_KEY: course_id})
    )
    context = {
        'my_badge_url': my_badge_url,
    }
    MandrillClient().send_mail(MandrillClient.USER_BADGE_EMAIL_TEMPLATE, user_email, context)
