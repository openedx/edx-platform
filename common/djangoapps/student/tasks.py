"""
This file contains celery tasks for sending email
"""


import logging

from celery.exceptions import MaxRetriesExceededError
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.errors import RecoverableChannelDeliveryError
from edx_ace.message import Message
from edx_django_utils.monitoring import set_code_owner_attribute
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request

log = logging.getLogger('edx.celery.task')


# This is a task function that is in the process of being renamed.
# In order to avoid dropping tasks during deployment, we have to register it twice,
# once under each name. This allows us to cut from one name to the other safely.
# Once we have fully switched to the new name, we can go back to registering
# this task function with a simple decorator.
@set_code_owner_attribute
def _send_activation_email(self, msg_string, from_address=None):
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


_OLD_TASK_NAME = 'student.send_activation_email'
_NEW_TASK_NAME = 'common.djangoapps.student.tasks.send_activation_email'


# Register task under both its old and new names,
# but expose only the old-named task for invocation.
# -> Next step: Once we deploy and teach Celery workers the new name,
#    set `send_activation_email` to the new-named task.
send_activation_email = shared_task(bind=True, name=_OLD_TASK_NAME)(_send_activation_email)
shared_task(bind=True, name=_NEW_TASK_NAME)(_send_activation_email)
