"""
Agreements API
"""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.agreements.models import IntegritySignature

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
