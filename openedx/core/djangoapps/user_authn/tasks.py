"""
This file contains celery tasks for sending email
"""

import hashlib
import logging
import math

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.errors import RecoverableChannelDeliveryError
from edx_ace.message import Message
from edx_django_utils.monitoring import set_code_owner_attribute
from rest_framework.status import HTTP_408_REQUEST_TIMEOUT

from common.djangoapps.track import segment
from openedx.core.djangoapps.password_policy.hibp import PwnedPasswordsAPI
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request

log = logging.getLogger('edx.celery.task')


def get_pwned_properties(pwned_response, password):
    """
    Derive different pwned parameters for analytics
    """
    properties = {}
    if pwned_response == HTTP_408_REQUEST_TIMEOUT:
        properties['vulnerability'] = 'unknown'
        pwned_count = 0
    else:
        pwned_count = pwned_response.get(password, 0)
        properties['vulnerability'] = 'yes' if pwned_count > 0 else 'no'

    if pwned_count > 0:
        properties['frequency'] = math.ceil(math.log10(pwned_count))

    return properties


@shared_task
def check_pwned_password_and_send_track_event(user_id, password, internal_user=False):
    """
    Check the Pwned Databases and send its event to Segment
    """
    try:
        password = hashlib.sha1(password.encode('utf-8')).hexdigest()
        pwned_response = PwnedPasswordsAPI.range(password)
        if pwned_response is not None:
            properties = get_pwned_properties(pwned_response, password)
            properties['internal_user'] = internal_user
            segment.track(user_id, 'edx.bi.user.pwned.password.status', properties)
    except Exception:  # pylint: disable=W0703
        log.exception(
            'Unable to get response from pwned password api for user_id: "%s"',
            user_id,
        )
        return None  # lint-amnesty, pylint: disable=raise-missing-from


@shared_task(bind=True)
@set_code_owner_attribute
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
    user = User.objects.get(id=msg.recipient.lms_user_id)

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
        raise Exception  # lint-amnesty, pylint: disable=raise-missing-from
