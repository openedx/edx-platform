"""
Utils for use in enrollment codebase such as views.
"""
import logging
from openedx.core.djangoapps.enrollments.utils import add_user_to_course_cohort, check_mode_and_enroll

from django.core.exceptions import ObjectDoesNotExist  # lint-amnesty, pylint: disable=wrong-import-order
from django.db import transaction
from common.djangoapps.student.models import User
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup, add_user_to_cohort, get_cohort_by_name
from openedx.core.djangoapps.enrollments import api
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError, CourseEnrollmentExistsError
from openedx.core.lib.log_utils import audit_log
from openedx.features.enterprise_support.enrollments.exceptions import (
    CourseIdMissingException,
    UserDoesNotExistException
)
from openedx.features.enterprise_support.api import (
    ConsentApiServiceClient,
    EnterpriseApiException,
    enterprise_enabled
)

from enterprise.api.v1.serializers import EnterpriseCourseEnrollmentWriteSerializer

REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}

log = logging.getLogger(__name__)


def enroll_user_in_course(username, course_id, mode, enrollment_attributes,
                          explicit_linked_enterprise,
                          cohort_name=None,
                          is_active=False,
                          has_api_key_permissions=False,
                          ):
    """
    Arguments:
     - username (str): User name
     - course_id (obj) : Course key obtained using CourseKey.from_string(course_id_input)
     - mode (CourseMode): course mode
     - explicit_linked_enterprise: uuid of enterprise
     - enrollment_attributes (dict): A dictionary that contains the following values.
        * namespace: Namespace of the attribute
        * name: Name of the attribute
        * value: Value of the attribute
    - cohort_name (str): Optional. If provided, user will be added to cohort
    - is_active (bool): Optional. A Boolean value that indicates whether the
        enrollment is active. Only server-to-server requests can
        deactivate an enrollment.
    - has_api_key_permissions: Default False, set to True for server calls
    """
    user = _validate_enrollment_inputs(username, course_id)

    with transaction.atomic():
        try:
            if explicit_linked_enterprise and enterprise_enabled():
                enroll_in_enterprise_and_provide_consent(
                    user,
                    course_id,
                    explicit_linked_enterprise
                )

            enrollment = api.get_enrollment(username, str(course_id))
            response = check_mode_and_enroll(username, course_id, mode, enrollment, enrollment_attributes, is_active, has_api_key_permissions)

            add_user_to_course_cohort(cohort_name, course_id, user)

            log.info('The user [%s] has already been enrolled in course run [%s].', username, course_id)
            return response
        except CourseEnrollmentExistsError as error:
            log.warning('An enrollment already exists for user [%s] in course run [%s].', username, course_id)
            raise error
        except CourseEnrollmentError as error:
            log.exception("An error occurred while creating the new course enrollment for user "
                          "[%s] in course run [%s]", username, course_id)
            raise error
        except CourseUserGroup.DoesNotExist as error:
            log.exception('Missing cohort [%s] in course run [%s]', cohort_name, course_id)
            raise error
        finally:
            # Assumes that the ecommerce service uses an API key to authenticate.
            if has_api_key_permissions:
                current_enrollment = api.get_enrollment(username, str(course_id))
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
    try:
        # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
        user = User.objects.get(username=username)
    except ObjectDoesNotExist as error:
        raise UserDoesNotExistException(f'The user {username} does not exist.') from error
    return user


def enroll_in_enterprise_and_provide_consent(user, course_id, enterprise_customer_uuid):
    """
    Enrolls a user in a course using enterprise_course_enrollment api if both of the flags are true
      - has_api_key_permissions, explicit_linked_enterprise
    """
    consent_client = ConsentApiServiceClient()
    try:
        serializer = EnterpriseCourseEnrollmentWriteSerializer({
            'username': user.username,
            'course_id': course_id,
        })
        if not serializer.is_valid():
            raise CourseEnrollmentError(str(serializer.errors))
        serializer.save()
    except EnterpriseApiException as error:
        log.exception("An unexpected error occurred while creating the new EnterpriseCourseEnrollment "
                      "for user id [%s] in course run [%s]", user.id, course_id)
        raise CourseEnrollmentError(str(error))  # lint-amnesty, pylint: disable=raise-missing-from
    kwargs = {
        'username': user.username,
        'course_id': str(course_id),
        'enterprise_customer_uuid': enterprise_customer_uuid,
    }
    consent_client.provide_consent(**kwargs)
