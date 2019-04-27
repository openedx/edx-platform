"""
This file contains celery tasks for sending email
"""
import logging

from celery.exceptions import MaxRetriesExceededError
from celery.task import task  # pylint: disable=no-name-in-module, import-error
from django.conf import settings
from edx_ace import ace
from edx_ace.errors import RecoverableChannelDeliveryError
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger('edx.celery.task')


@task(bind=True)
def send_activation_email(self, msg, from_address=None):
    """
    Sending an activation email to the user.
    """
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    retries = self.request.retries

    if from_address is None:
        from_address = configuration_helpers.get_value('ACTIVATION_EMAIL_FROM_ADDRESS') or (
            configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        )
    msg.options['from_address'] = from_address

    dest_addr = msg.recipient.email_address

    try:
        ace.send(msg)
        # Log that the Activation Email has been sent to user without an exception
        log.info("Activation Email has been sent to User {user_email}".format(
            user_email=dest_addr
        ))
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
    except Exception:  # pylint: disable=bare-except
        log.exception(
            'Unable to send activation email to user from "%s" to "%s"',
            from_address,
            dest_addr,
            exc_info=True
        )
        raise Exception
