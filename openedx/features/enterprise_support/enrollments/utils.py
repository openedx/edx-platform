"""
Utils for use in enrollment codebase such as views.
"""
import logging

from django.core.exceptions import ObjectDoesNotExist  # lint-amnesty, pylint: disable=wrong-import-order
from django.db import transaction

from common.djangoapps.student.models import User
from openedx.core.djangoapps.enrollments import api as enrollment_api
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError, CourseEnrollmentExistsError
from openedx.core.lib.log_utils import audit_log
from openedx.features.enterprise_support.enrollments.exceptions import (
    CourseIdMissingException,
    UserDoesNotExistException
)

log = logging.getLogger(__name__)


def lms_enroll_user_in_course(
    username,
    course_id,
    mode,
    enterprise_uuid,
    is_active=True,
):
    """
    Enrollment function meant to be called by edx-enterprise to replace the
    current uses of the EnrollmentApiClient
    The REST enrollment endpoint may also eventually also want to reuse this function
    since it's a subset of what the endpoint handles

    Unlike the REST endpoint, this function does not check for enterprise enabled, or user api key
    permissions etc. Those concerns are still going to be used by REST endpoint but this function
    is meant for use from within edx-enterprise hence already presume such privileges.

    Arguments:
     - username (str): User name
     - course_id (obj) : Course key obtained using CourseKey.from_string(course_id_input)
     - mode (CourseMode): course mode
     - enterprise_uuid (str): id to identify the enterprise to enroll under
     - is_active (bool): Optional. A Boolean value that indicates whether the
        enrollment is to be set to inactive (if False). Usually we want a True if enrolling anew.

    Returns: A serializable dictionary of the new course enrollment. If it hits
     `CourseEnrollmentExistsError` then it logs the error and returns None.
    """
    user = _validate_enrollment_inputs(username, course_id)

    with transaction.atomic():
        try:
            response = enrollment_api.add_enrollment(
                username,
                str(course_id),
                mode=mode,
                is_active=is_active,
                enrollment_attributes=None,
                enterprise_uuid=enterprise_uuid,
            )
            log.info('The user [%s] has been enrolled in course run [%s].', username, course_id)
            return response
        except CourseEnrollmentExistsError as error:  # pylint: disable=unused-variable
            log.warning('An enrollment already exists for user [%s] in course run [%s].', username, course_id)
            return None
        except CourseEnrollmentError as error:
            log.exception("An error occurred while creating the new course enrollment for user "
                          "[%s] in course run [%s]", username, course_id)
            raise error
        finally:
            # Assumes that the ecommerce service uses an API key to authenticate.
            current_enrollment = enrollment_api.get_enrollment(username, str(course_id))
            audit_log(
                'enrollment_change_requested',
                course_id=str(course_id),
                requested_mode=mode,
                actual_mode=current_enrollment['mode'] if current_enrollment else None,
                requested_activation=is_active,
                actual_activation=current_enrollment['is_active'] if current_enrollment else None,
                user_id=user.id
            )


def _validate_enrollment_inputs(username, course_id):
    """
    Validates username and course_id.
    Raises:
     - UserDoesNotExistException if user not found.
     - CourseIdMissingException if course_id not provided.
    """
    if not course_id:
        raise CourseIdMissingException("Course ID must be specified to create a new enrollment.")
    if not username:
        raise UserDoesNotExistException('username is a required argument for enrollment')
    try:
        # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
        user = User.objects.get(username=username)
    except ObjectDoesNotExist as error:
        raise UserDoesNotExistException(f'The user {username} does not exist.') from error
    return user
