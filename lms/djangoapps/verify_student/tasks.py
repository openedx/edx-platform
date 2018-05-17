"""
This file contains celery tasks for sending status email asynchronously
"""
from django.conf import settings
from celery.task import task

from lms.djangoapps.verify_student.utils import send_verification_status_email

ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


@task(routing_key=ACE_ROUTING_KEY)
def compose_and_send_expired_status_email(user, context):
    """
    Compose context and send expired verification status email to a learner.

    Arguments:
            user: A user instance
            context: context containing required parameters for sending email
    """
    context['email'] = user.email
    send_verification_status_email(context)
