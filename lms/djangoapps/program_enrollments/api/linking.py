"""
Python API function to link program enrollments and external_student_keys to an
LMS user.

Outside of this subpackage, import these functions
from `lms.djangoapps.program_enrollments.api`.
"""
from __future__ import absolute_import, unicode_literals

import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from student.models import CourseEnrollmentException

from .reading import fetch_program_enrollments
from .writing import enroll_in_masters_track

logger = logging.getLogger(__name__)
User = get_user_model()


NO_PROGRAM_ENROLLMENT_TEMPLATE = (
    'No program enrollment found for program uuid={program_uuid} and external student '
    'key={external_student_key}'
)
NO_LMS_USER_TEMPLATE = 'No user found with username {}'
EXISTING_USER_TEMPLATE = (
    'Program enrollment with external_student_key={external_student_key} is already linked to '
    '{account_relation} account username={username}'
)


@transaction.atomic
def link_program_enrollments(program_uuid, external_keys_to_usernames):
    """
    Utility function to link ProgramEnrollments to LMS Users

    Arguments:
        -program_uuid: the program for which we are linking program enrollments
        -external_keys_to_usernames: dict mapping `external_user_keys` to LMS usernames.

    Returns: dict[str: str]
        Map from external keys to errors, for the external keys of users whose
        linking produced errors.

    Raises: ValueError if None is included in external_keys_to_usernames

    This function will look up program enrollments and users, and update the program
    enrollments with the matching user. If the program enrollment has course enrollments, we
    will enroll the user into their waiting program courses.

    For each external_user_key:lms_username, if:
        - The user is not found
        - No enrollment is found for the given program and external_user_key
        - The enrollment already has a user
    An error message will be logged, and added to a dictionary of error messages keyed by
    external_key. The input will be skipped. All other inputs will be processed and
    enrollments updated, and then the function will return the dictionary of error messages.

    If there is an error while enrolling a user in a waiting program course enrollment, the
    error will be logged, and added to the returned error dictionary, and we will roll back all
    transactions for that user so that their db state will be the same as it was before this
    function was called, to prevent program enrollments to be in a state where they have an LMS
    user but still have waiting course enrollments. All other inputs will be processed
    normally.
    """
    errors = {}
    program_enrollments = _get_program_enrollments_by_ext_key(
        program_uuid, external_keys_to_usernames.keys()
    )
    users_by_username = _get_lms_users(external_keys_to_usernames.values())
    for external_student_key, username in external_keys_to_usernames.items():
        program_enrollment = program_enrollments.get(external_student_key)
        user = users_by_username.get(username)
        if not user:
            error_message = NO_LMS_USER_TEMPLATE.format(username)
        elif not program_enrollment:
            error_message = NO_PROGRAM_ENROLLMENT_TEMPLATE.format(
                program_uuid=program_uuid,
                external_student_key=external_student_key
            )
        elif program_enrollment.user:
            error_message = _user_already_linked_message(program_enrollment, user)
        else:
            error_message = None
        if error_message:
            logger.warning(error_message)
            errors[external_student_key] = error_message
            continue
        try:
            with transaction.atomic():
                link_program_enrollment_to_lms_user(program_enrollment, user)
        except (CourseEnrollmentException, IntegrityError) as e:
            logger.exception("Rolling back all operations for {}:{}".format(
                external_student_key,
                username,
            ))
            error_message = type(e).__name__
            if str(e):
                error_message += ': '
                error_message += str(e)
            errors[external_student_key] = error_message
    return errors


def _user_already_linked_message(program_enrollment, user):
    """
    Creates an error message that the specified program enrollment is already linked to an lms user
    """
    existing_username = program_enrollment.user.username
    external_student_key = program_enrollment.external_user_key
    return EXISTING_USER_TEMPLATE.format(
        external_student_key=external_student_key,
        account_relation='target' if program_enrollment.user.id == user.id else 'a different',
        username=existing_username,
    )


def _get_program_enrollments_by_ext_key(program_uuid, external_student_keys):
    """
    Does a bulk read of ProgramEnrollments for a given program and list of external student keys
    and returns a dict keyed by external student key
    """
    program_enrollments = fetch_program_enrollments(
        program_uuid=program_uuid,
        external_user_keys=external_student_keys,
    ).prefetch_related(
        'program_course_enrollments'
    ).select_related('user')
    return {
        program_enrollment.external_user_key: program_enrollment
        for program_enrollment in program_enrollments
    }


def _get_lms_users(lms_usernames):
    """
    Does a bulk read of Users by username and returns a dict keyed by username
    """
    return {
        user.username: user
        for user in User.objects.filter(username__in=lms_usernames)
    }


def link_program_enrollment_to_lms_user(program_enrollment, user):
    """
    Attempts to link the given program enrollment to the given user
    If the enrollment has any program course enrollments, enroll the user in those courses as well

    Raises: CourseEnrollmentException if there is an error enrolling user in a waiting
            program course enrollment
            IntegrityError if we try to create invalid records.
    """
    link_log_info = 'user id={} with external_user_key={} for program uuid={}'.format(
        user.id,
        program_enrollment.external_user_key,
        program_enrollment.program_uuid,
    )
    logger.info("Linking " + link_log_info)
    program_enrollment.user = user
    try:
        program_enrollment.save()
        program_course_enrollments = program_enrollment.program_course_enrollments.all()
        for pce in program_course_enrollments:
            pce.course_enrollment = enroll_in_masters_track(
                user, pce.course_key, pce.status
            )
            pce.save()
    except IntegrityError:
        logger.error("Integrity error while linking " + link_log_info)
        raise
    except CourseEnrollmentException as e:
        logger.error(
            "CourseEnrollmentException while linking {}: {}".format(
                link_log_info, str(e)
            )
        )
        raise
