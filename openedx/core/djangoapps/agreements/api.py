"""
Agreements API
"""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.agreements.models import IntegritySignature
from openedx.core.djangoapps.agreements.models import LTIPIITool
from openedx.core.djangoapps.agreements.models import LTIPIISignature

from .data import LTIToolsReceivingPIIData

log = logging.getLogger(__name__)
User = get_user_model()


def create_integrity_signature(username, course_id):
    """
    Create an integrity signature. If a signature already exists, do not create a new one.

    Arguments:
        * username (str)
        * course_id (str)

    Returns:
        * IntegritySignature object
    """
    user = User.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)
    signature, created = IntegritySignature.objects.get_or_create(user=user, course_key=course_key)
    if not created:
        log.warning(
            'Integrity signature already exists for user_id={user_id} and '
            'course_id={course_id}'.format(user_id=user.id, course_id=course_id)
        )
    return signature


def get_integrity_signature(username, course_id):
    """
    Get an integrity signature.

    Arguments:
        * username (str)
        * course_id (str)

    Returns:
        * An IntegritySignature object, or None if one does not exist for the
          user + course combination.
    """
    user = User.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)
    try:
        return IntegritySignature.objects.get(user=user, course_key=course_key)
    except ObjectDoesNotExist:
        return None


def get_integrity_signatures_for_course(course_id):
    """
    Get all integrity signatures for a given course.

    Arguments:
        * course_id (str)

    Returns:
        * QuerySet of IntegritySignature objects (can be empty).
    """
    course_key = CourseKey.from_string(course_id)
    return IntegritySignature.objects.filter(course_key=course_key)


def get_lti_tools_receiving_pii(course_id):
    """
    Get a course's LTI tools that share PII.

    Arguments:
        * course_id (str)

    Returns:
        * A List of LTI tools sharing PII.
    """

    course_key = CourseKey.from_string(course_id)
    course_ltipiitools = LTIPIITool.objects.get(course_key=course_key)

    return LTIToolsReceivingPIIData(
        lii_tools_receiving_pii=course_ltipiitools,
    )


def user_lit_pii_signature_needed(username, course_id):
    """
    Determines if a user needs to acknowledge the LTI PII Agreement

    Arguments:
        * username (str)

    Returns:
        * True if the user needs to sign a new acknowledgement.
        * False if the acknowledgements are up to date.
    """
    if _course_has_lti_pii_tools(course_id):
        if _user_lti_pii_signature_exists(username, course_id):
            if _user_needs_signature_update(username, course_id):
                # up to date
                return False
            else:
                # lti pii signature needs to be updated
                return True
        else:
            # write a new lti pii signature
            return True
    else:
        return False


def _course_has_lti_pii_tools(course_id):
    """
    Determines if a specifc course has lti tools sharing pii

    Arguments:
        * course_id (str)

    Returns:
        * True if the course does have a list.
        * False if the course does not.
    """
    course_key = CourseKey.from_string(course_id)
    course_lti_pii_tools = LTIPIITool.objects.get(course_key)

    if not course_lti_pii_tools:
        # empty queryset, meaning no tools
        return False
    else:
        return True


def _user_lti_pii_signature_exists(username, course_id):
    """
    Determines if a user's lti pii signature exists for a specfic course

    Arguments:
        * username (str)
        * course_id (str)

    Returns:
        * True if user has a signature for the given course.
        * False if the user does not have a signature for the given course.
    """
    user = User.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)

    signature = LTIPIISignature.objects.get(user=user, course_key=course_key)
    if not signature:
        return False
    else:
        return True


def _user_needs_signature_update(username, course_id):
    """
        Determines if a user's existing lti pii signature is out-of-date for a given course.

        Arguments:
            * username (str)
            * course_id (str)

        Returns:
            * True if user has a signature for the given course.
            * False if the user does not have a signature for the given course.
        """

    user = User.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)

    user_lti_pii_signature_hash = LTIPIISignature.objects.get(course_key=course_key, user=user).lti_tools_hash
    course_lti_pii_tools_hash = LTIPIITool.objects.get(course_key=course_key).lti_tools_hash

    if (user_lti_pii_signature_hash == course_lti_pii_tools_hash):
        # Hashes are equal, therefor update is not need
        return False
    else:
        return True
