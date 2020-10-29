"""
Python API function to link program enrollments and external_student_keys to an
LMS user.

Outside of this subpackage, import these functions
from `lms.djangoapps.program_enrollments.api`.
"""
from __future__ import absolute_import, unicode_literals

import logging
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from student.models import CourseEnrollmentException

from .reading import fetch_program_enrollments

logger = logging.getLogger(__name__)
User = get_user_model()


NO_PROGRAM_ENROLLMENT_TEMPLATE = (
    'No program enrollment found for program uuid={program_uuid} and external student '
    'key={external_student_key}'
)
NO_LMS_USER_TEMPLATE = 'No user found with username {}'
COURSE_ENROLLMENT_ERR_TEMPLATE = (
    'Failed to enroll user {user} with waiting program course enrollment for course {course}'
)
EXISTING_USER_TEMPLATE = (
    'Program enrollment with external_student_key={external_student_key} is already linked to '
    '{account_relation} account username={username}'
)


@transaction.atomic
def link_program_enrollments_to_lms_users(program_uuid, external_keys_to_usernames):
    """
        Utility function to link ProgramEnrollments to LMS Users

        Arguments:
            -program_uuid: the program for which we are linking program enrollments
            -external_keys_to_usernames: dict mapping `external_user_keys` to LMS usernames.

        Returns:
            {
                (external_key, username): Error message if there was an error
            }

        Raises: ValueError if None is included in external_keys_to_usernames

        This function will look up program enrollments and users, and update the program
        enrollments with the matching user. If the program enrollment has course enrollments, we
        will enroll the user into their waiting program courses.

        For each external_user_key:lms_username, if:
            - The user is not found
            - No enrollment is found for the given program and external_user_key
            - The enrollment already has a user
        An error message will be logged, and added to a dictionary of error messages keyed by
        (external_key, username). The input will be skipped. All other inputs will be processed and
        enrollments updated, and then the function will return the dictionary of error messages.

        If there is an error while enrolling a user in a waiting program course enrollment, the
        error will be logged, and added to the returned error dictionary, and we will roll back all
        transactions for that user so that their db state will be the same as it was before this
        function was called, to prevent program enrollments to be in a state where they have an LMS
        user but still have waiting course enrollments. All other inputs will be processed
        normally.
    """
    _validate_inputs(program_uuid, external_keys_to_usernames)
    errors = {}
    program_enrollments = _get_program_enrollments_by_ext_key(
        program_uuid, external_keys_to_usernames.keys()
    )
    users = _get_lms_users(external_keys_to_usernames.values())
    for item in external_keys_to_usernames.items():
        external_student_key, username = item

        user = users.get(username)
        error_message = None
        if not user:
            error_message = NO_LMS_USER_TEMPLATE.format(username)

        program_enrollment = program_enrollments.get(external_student_key)
        if not program_enrollment:
            error_message = NO_PROGRAM_ENROLLMENT_TEMPLATE.format(
                program_uuid=program_uuid,
                external_student_key=external_student_key
            )
        elif program_enrollment.user:
            error_message = user_already_linked_message(program_enrollment, user)

        if error_message:
            logger.warning(error_message)
            errors[item] = error_message
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
            errors[item] = error_message
    return errors


def link_program_enrollment_to_lms_user(program_enrollment, user):
    """
    Attempts to link the given program enrollment to the given user
    If the enrollment has any program course enrollments, enroll the user in those courses as well

    Raises: CourseEnrollmentException if there is an error enrolling user in a waiting
            program course enrollment
            IntegrityError if we try to create invalid records.
    """
    try:
        _link_program_enrollment(program_enrollment, user)
        _link_course_enrollments(program_enrollment, user)
    except IntegrityError:
        logger.exception("Integrity error while linking program enrollments")
        raise


def user_already_linked_message(program_enrollment, user):
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


def _validate_inputs(program_uuid, external_keys_to_usernames):
    if None in external_keys_to_usernames or None in external_keys_to_usernames.values():
        raise ValueError('external_user_key or username cannot be None')
    UUID(str(program_uuid))  # raises ValueError if invalid


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


def _link_program_enrollment(program_enrollment, user):
    """
    Links program enrollment to user.

    Raises IntegrityError if ProgramEnrollment is invalid
    """
    logger.info('Linking external student key {} and user {}'.format(
        program_enrollment.external_user_key,
        user.username
    ))
    program_enrollment.user = user
    program_enrollment.save()


def _link_course_enrollments(program_enrollment, user):
    """
    Enrolls user in waiting program course enrollments

    Raises:
        IntegrityError if a constraint is violated
        CourseEnrollmentException if there is an issue enrolling the user in a course
    """
    try:
        for program_course_enrollment in program_enrollment.program_course_enrollments.all():
            program_course_enrollment.enroll(user)
    except CourseEnrollmentException as e:
        error_message = COURSE_ENROLLMENT_ERR_TEMPLATE.format(
            user=user.username,
            course=program_course_enrollment.course_key
        )
        logger.exception(error_message)
        raise type(e)(error_message)
