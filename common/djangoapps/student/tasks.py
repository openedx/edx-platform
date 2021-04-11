"""
This file contains celery tasks for sending email
"""


import logging

from celery.exceptions import MaxRetriesExceededError
from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.errors import RecoverableChannelDeliveryError
from edx_ace.message import Message
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request

log = logging.getLogger('edx.celery.task')


@task(bind=True, name='student.send_activation_email')
def send_activation_email(self, msg_string, from_address=None):
    """
    Sending an activation email to the user.
    """
    msg = Message.from_string(msg_string)

    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    retries = self.request.retries

    if from_address is None:
        from_address = configuration_helpers.get_value('ACTIVATION_EMAIL_FROM_ADDRESS') or (
            configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        )
    msg.options['from_address'] = from_address

    dest_addr = msg.recipient.email_address

    site = Site.objects.get_current()
    user = User.objects.get(username=msg.recipient.username)

    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except RecoverableChannelDeliveryError:
        log.info('Retrying sending email to user {dest_addr}, attempt # {attempt} of {max_attempts}'.format(
            dest_addr=dest_addr,
            attempt=retries,
            max_attempts=max_retries
        ))
        try:
            self.retry(countdown=settings.RETRY_ACTIVATION_EMAIL_TIMEOUT, max_retries=max_retries)
        except MaxRetriesExceededError:
            log.error(
                'Unable to send activation email to user from "%s" to "%s"',
                from_address,
                dest_addr,
                exc_info=True
            )
    except Exception:
        log.exception(
            'Unable to send activation email to user from "%s" to "%s"',
            from_address,
            dest_addr,
        )
        raise Exception
