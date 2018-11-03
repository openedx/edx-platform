# -*- coding: utf-8 -*-
"""
Common Utilities for the verify_student application.
"""

import datetime
import logging
import pytz

from django.conf import settings
from sailthru import SailthruClient

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
