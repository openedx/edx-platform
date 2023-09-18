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
from .data import LTIPIISignatureData

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


def create_lti_pii_signature(username, course_id, lti_tools):
    """
    Creates an lti pii tool signature. If the signature already exist, do not create a new one.

    Arguments:
        * course_key (str)
        * lti_tools (dict)
        * lti_tools_hash (int)
    Returns:
        * An LTIPIISignature, or None if a signature already exists.
    """
    user = User.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)
    lti_tools_hash = hash(str(lti_tools))

    # if user and course exists, update, otherwise create a new signature
    try:
        LTIPIISignature.objects.get(user=user, course_key=course_key)
    except ObjectDoesNotExist:
        #create
        signature = LTIPIISignature.objects.create(
            user=user,
            course_key=course_key,
            lti_tools=lti_tools,
            lti_tools_hash=lti_tools_hash)
        return signature
    else:
        signature = LTIPIISignature.objects.update(
            user=user,
            course_key=course_key,
            lti_tools=lti_tools,
            lti_tools_hash=lti_tools_hash)
        return signature


def get_lti_pii_signature(username, course_id):
    """
    Get the lti pii signature of a user in a course.

    Arguments:
        * username (str)
        * course_id (str)

    Returns:
        * An LTIPIISignature object, or None if one does not exist for the
          user + course combination.
    """
    course_key = CourseKey.from_string(course_id)
    try:
        user = User.objects.get(username=username)
        signature = LTIPIISignature.objects.get(user=user, course_key=course_key)
    except ObjectDoesNotExist:
        return None
    else:
        return LTIPIISignatureData(user=signature.user, course_id=str(signature.course_key),
                                   lti_tools=signature.lti_tools, lti_tools_hash=signature.lti_tools_hash)


def get_pii_receiving_lti_tools(course_id):
    """
    Get a course's LTI tools that share PII.

    Arguments:
        * course_id (str)

    Returns:
        * A List of LTI tools sharing PII.
    """

    course_key = CourseKey.from_string(course_id)
    try:
        course_ltipiitools = LTIPIITool.objects.get(course_key=course_key).lti_tools
        return LTIToolsReceivingPIIData(
            lii_tools_receiving_pii=course_ltipiitools,
        )
    except ObjectDoesNotExist:
        return None


def user_lti_pii_signature_needed(username, course_id):
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
    try:
        LTIPIITool.objects.get(course_key)
    except ObjectDoesNotExist:
        # no entry in the database
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
    course_key = CourseKey.from_string(course_id)

    try:
        user = User.objects.get(username=username)
        LTIPIISignature.objects.get(user=user, course_key=course_key)
    except ObjectDoesNotExist:
        return None
    else:
        return True  # signature exist


def _user_needs_signature_update(username, course_id):
    """
        Determines if a user's existing lti pii signature is out-of-date for a given course.

        Arguments:
            * username (str)
            * course_id (str)

        Returns:
            * True if user needs a new signature
            * False if the user has an up-to-date signature.
        """
    course_key = CourseKey.from_string(course_id)

    try:
        user = User.objects.get(username=username)
        user_lti_pii_signature_hash = LTIPIISignature.objects.get(course_key=course_key, user=user).lti_tools_hash
        course_lti_pii_tools_hash = LTIPIITool.objects.get(course_key=course_key).lti_tools_hash
    except ObjectDoesNotExist:
        return None
    else:
        if user_lti_pii_signature_hash == course_lti_pii_tools_hash:
            # Hashes are equal, therefore update is not need
            return False
        else:
            return True
