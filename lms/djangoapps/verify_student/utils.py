"""
Common Utilities for the verify_student application.
"""

import datetime
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)


def send_verification_status_email(context):
    """
    Send an email to inform learners about their verification status
    """
    current_date = datetime.datetime.now()
    date = "{}/{}/{}".format(current_date.month, current_date.day, current_date.year)
    email_template_context = {
        'full_name': context['user'].profile.name,
        'platform_name': configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
        'date': date
    }

    subject = context['subject']
    message = render_to_string(context['message'], email_template_context)
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    to_address = context['user'].email

    try:
        send_mail(subject, message, from_address, [to_address], fail_silently=False)
    except:  # pylint: disable=bare-except
        # We catch all exceptions and log them.
        # It would be much, much worse to roll back the transaction due to an uncaught
        # exception than to skip sending the notification email.
        log.exception(
            _("Could not send verification status email having {subject} subject for user {user}").format(
                subject=context['subject'],
                user=context['user'].id
            ))
