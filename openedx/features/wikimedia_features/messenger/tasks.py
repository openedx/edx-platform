from logging import getLogger
from celery import task
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth.models import User

from openedx.features.wikimedia_features.email.utils import send_unread_messages_email

log = getLogger(__name__)


@task(base=LoggedTask)
def send_unread_messages_email_task(data):
    try:
        request_user = User.objects.get(username=settings.EMAIL_ADMIN)
        for username, context in data.items():
            user = User.objects.get(username=username)
            send_unread_messages_email(user, context, request_user)
    except User.DoesNotExist:
        log.error(
            "Unable to send email as Email Admin User with username: {} does not exist.".format(settings.EMAIL_ADMIN)
        )
