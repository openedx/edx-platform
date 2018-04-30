# -*- coding: utf-8 -*-
"""
Common Utilities for the verify_student application.
"""

import datetime
import logging
import pytz

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)


def is_verification_expiring_soon(expiration_datetime):
    """
    Returns True if verification is expiring within EXPIRING_SOON_WINDOW.
    """
    if expiration_datetime:
        if (expiration_datetime - datetime.datetime.now(pytz.UTC)).days <= settings.VERIFY_STUDENT.get(
                "EXPIRING_SOON_WINDOW"):
            return True

    return False


def earliest_allowed_verification_date():
    """
    Returns the earliest allowed date given the settings
    """
    days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
    return datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=days_good_for)


def verification_for_datetime(deadline, candidates):
    """Find a verification in a set that applied during a particular datetime.

    A verification is considered "active" during a datetime if:
    1) The verification was created before the datetime, and
    2) The verification is set to expire after the datetime.

    Note that verification status is *not* considered here,
    just the start/expire dates.

    If multiple verifications were active at the deadline,
    returns the most recently created one.

    Arguments:
        deadline (datetime): The datetime at which the verification applied.
            If `None`, then return the most recently created candidate.
        candidates (list of `PhotoVerification`s): Potential verifications to search through.

    Returns:
        PhotoVerification: A photo verification that was active at the deadline.
            If no verification was active, return None.

    """
    if not candidates:
        return None

    # If there's no deadline, then return the most recently created verification
    if deadline is None:
        return candidates[0]

    # Otherwise, look for a verification that was in effect at the deadline,
    # preferring recent verifications.
    # If no such verification is found, implicitly return `None`
    for verification in candidates:
        if verification.active_at_datetime(deadline):
            return verification


def send_verification_status_email(context):
    """
    Send an email to inform learners about their verification status
    """
    subject = context['subject']
    message = render_to_string(context['message'], context['email_template_context'])
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    to_address = context['email']

    try:
        send_mail(subject, message, from_address, [to_address], fail_silently=False)
    except:  # pylint: disable=bare-except
        # We catch all exceptions and log them.
        # It would be much, much worse to roll back the transaction due to an uncaught
        # exception than to skip sending the notification email.
        log.exception(
            _("Could not send verification status email having subject: {subject} and email of user: {email}").format(
                subject=context['subject'],
                email=context['email']
            ))


def most_recent_verification(photo_id_verifications, sso_id_verifications, most_recent_key):
    """
    Return the most recent verification given querysets for both photo and sso verifications.

    Arguments:
            photo_id_verifications: Queryset containing photo verifications
            sso_id_verifications: Queryset containing sso verifications
            most_recent_key: Either 'updated_at' or 'created_at'

    Returns:
        The most recent verification.
    """
    photo_id_verification = photo_id_verifications and photo_id_verifications.first()
    sso_id_verification = sso_id_verifications and sso_id_verifications.first()

    if not photo_id_verification and not sso_id_verification:
        return None
    elif photo_id_verification and not sso_id_verification:
        return photo_id_verification
    elif sso_id_verification and not photo_id_verification:
        return sso_id_verification
    elif getattr(photo_id_verification, most_recent_key) > getattr(sso_id_verification, most_recent_key):
        return photo_id_verification
    else:
        return sso_id_verification
