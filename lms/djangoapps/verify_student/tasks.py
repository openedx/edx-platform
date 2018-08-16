"""
Django Celery tasks for service status app
"""
import logging
from smtplib import SMTPException

from celery import task
from django.conf import settings
from django.core.mail import send_mail

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
log = logging.getLogger(__name__)


@task(routing_key=ACE_ROUTING_KEY)
def send_verification_status_email(context):
    """
    Spins a task to send verification status email to the learner
    """
    subject = context.get('subject')
    message = render_to_string(context.get('template'), context.get('email_vars'))
    from_addr = configuration_helpers.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )
    dest_addr = context.get('email')

    try:
        send_mail(
            subject,
            message,
            from_addr,
            [dest_addr],
            fail_silently=False
        )
    except SMTPException:
        log.warning("Failure in sending verification status e-mail to %s", dest_addr)
