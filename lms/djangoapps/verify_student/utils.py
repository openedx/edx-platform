# -*- coding: utf-8 -*-
"""
Common Utilities for the verify_student application.
"""

import datetime
import logging

from django.conf import settings
from django.utils.timezone import now

from six import text_type

from lms.djangoapps.verify_student.tasks import send_request_to_ss_for_user

log = logging.getLogger(__name__)


def submit_request_to_ss(user_verification, copy_id_photo_from):
    """
    Submit our verification attempt to Software Secure for validation.

    Submits the task to software secure and If the task creation fails,
    set the verification status to "must_retry".
    """
    try:
        send_request_to_ss_for_user.delay(
            user_verification_id=user_verification.id, copy_id_photo_from=copy_id_photo_from
        )
    except Exception as error:  # pylint: disable=broad-except
        log.error(
            "Software Secure submit request %r failed, result: %s", user_verification.user.username, text_type(error)
        )
        user_verification.mark_must_retry()


def is_verification_expiring_soon(expiration_datetime):
    """
    Returns True if verification is expiring within EXPIRING_SOON_WINDOW.
    """
    if expiration_datetime:
        if (expiration_datetime - now()).days <= settings.VERIFY_STUDENT.get("EXPIRING_SOON_WINDOW"):
            return True

    return False


def earliest_allowed_verification_date():
    """
    Returns the earliest allowed date given the settings
    """
    days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
    return now() - datetime.timedelta(days=days_good_for)


def active_verifications(candidates, deadline):
    """
    Based on the deadline, only return verification attempts
    that are considered active (non-expired and wasn't created for future)
    """
    relevant_attempts = []
    if not candidates:
        return relevant_attempts

    # Look for a verification that was in effect at the deadline,
    # preferring recent verifications.
    # If no such verification is found, implicitly return empty array
    for verification in candidates:
        if verification.active_at_datetime(deadline):
            relevant_attempts.append(verification)

    return relevant_attempts


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

    if not deadline:
        return candidates[0]

    attempts = active_verifications(candidates, deadline)
    if attempts:
        return attempts[0]
    else:
        return None


def most_recent_verification(photo_id_verifications, sso_id_verifications, manual_id_verifications, most_recent_key):
    """
    Return the most recent verification given querysets for photo, sso and manual verifications.

    This function creates a map of the latest verification of all types and then returns the earliest
    verification using the max of the map values.

    Arguments:
        photo_id_verifications: Queryset containing photo verifications
        sso_id_verifications: Queryset containing sso verifications
        manual_id_verifications: Queryset containing manual verifications
        most_recent_key: Either 'updated_at' or 'created_at'

    Returns:
        The most recent verification.
    """
    photo_id_verification = photo_id_verifications and photo_id_verifications.first()
    sso_id_verification = sso_id_verifications and sso_id_verifications.first()
    manual_id_verification = manual_id_verifications and manual_id_verifications.first()

    verifications = [photo_id_verification, sso_id_verification, manual_id_verification]

    verifications_map = {
        verification: getattr(verification, most_recent_key)
        for verification in verifications
        if getattr(verification, most_recent_key, False)
    }

    return max(verifications_map, key=lambda k: verifications_map[k]) if verifications_map else None


def auto_verify_for_testing_enabled(override=None):
    """
    If AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING is True, we want to skip posting
    anything to Software Secure.

    Bypass posting anything to Software Secure if auto verify feature for testing is enabled.
    We actually don't even create the message because that would require encryption and message
    signing that rely on settings.VERIFY_STUDENT values that aren't set in dev. So we just
    pretend like we successfully posted.
    """
    if override is not None:
        return override
    return settings.FEATURES.get('AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING')


def can_verify_now(verification_status, expiration_datetime):
    """
    Returns whether one is eligible for verification now based on status and expiration.

    Arguments:
        verification_status (str)
        expiration_datetime (datetime)

    Returns: bool
    """
    return (
        # If the user has no initial verification or if the verification
        # process is still ongoing 'pending' or expired then allow the user to
        # submit the photo verification.
        # A photo verification is marked as 'pending' if its status is either
        # 'submitted' or 'must_retry'.
        verification_status['status'] in {"none", "must_reverify", "expired", "pending"}
        or (
            # The user has an active verification, but the verification
            # is set to expire within "EXPIRING_SOON_WINDOW" days (default is 4 weeks).
            # In this case user can resubmit photos for reverification.
            expiration_datetime
            and is_verification_expiring_soon(expiration_datetime)
        )
    )
