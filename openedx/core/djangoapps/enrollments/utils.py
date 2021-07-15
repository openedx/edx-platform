import logging

from django.core.exceptions import ObjectDoesNotExist  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys import InvalidKeyError  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys.edx.keys import CourseKey  # lint-amnesty, pylint: disable=wrong-import-order

from common.djangoapps.student.models import User
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup, add_user_to_cohort, get_cohort_by_name
from openedx.core.djangoapps.enrollments import api
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError, CourseEnrollmentExistsError
from openedx.core.djangoapps.enrollments.exceptions import (
    CourseIdMissingException,
    EnrollmentAttributesMissingError,
    EnrollmentModeMismatchError,
    UserDoesNotExistException
)
from openedx.core.lib.exceptions import CourseNotFoundError
from openedx.core.lib.log_utils import audit_log
from openedx.features.enterprise_support.api import (
    ConsentApiServiceClient,
    EnterpriseApiException,
    EnterpriseApiServiceClient,
    enterprise_enabled
)

REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}

log = logging.getLogger(__name__)


def enroll_user_in_course(
    username,
    course_id,
    mode,
    enrollment_attributes,
    cohort_name=None,
    is_active=False,
    has_global_staff_status=False,
    has_api_key_permissions=False,
    explicit_linked_enterprise=False,
):
    if not course_id:
        raise CourseIdMissingException("Course ID must be specified to create a new enrollment.")
    try:
        course_id = CourseKey.from_string(course_id)
    except InvalidKeyError:
        raise CourseNotFoundError(f"No course '{course_id}' found for enrollment")
    try:
        # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        raise UserDoesNotExistException(f'The user {username} does not exist.')

    try:
        if explicit_linked_enterprise and has_api_key_permissions and enterprise_enabled():
            enterprise_api_client = EnterpriseApiServiceClient()
            consent_client = ConsentApiServiceClient()
            try:
                enterprise_api_client.post_enterprise_course_enrollment(username, str(course_id), None)
            except EnterpriseApiException as error:
                log.exception("An unexpected error occurred while creating the new EnterpriseCourseEnrollment "
                              "for user [%s] in course run [%s]", username, course_id)
                raise CourseEnrollmentError(str(error))  # lint-amnesty, pylint: disable=raise-missing-from
            kwargs = {
                'username': username,
                'course_id': str(course_id),
                'enterprise_customer_uuid': explicit_linked_enterprise,
            }
            consent_client.provide_consent(**kwargs)

        enrollment = api.get_enrollment(username, str(course_id))
        mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
        active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
        missing_attrs = []
        if enrollment_attributes:
            actual_attrs = [
                "{namespace}:{name}".format(**attr)
                for attr in enrollment_attributes
            ]
            missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
        if (has_global_staff_status or has_api_key_permissions) and (mode_changed or active_changed):
            if mode_changed and active_changed and not is_active:
                # if the requester wanted to deactivate but specified the wrong mode, fail
                # the request (on the assumption that the requester had outdated information
                # about the currently active enrollment).
                msg = "Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                    enrollment["mode"], mode
                )
                log.warning(msg)
                raise EnrollmentModeMismatchError(msg)
            if missing_attrs:
                msg = "Missing enrollment attributes: requested mode={} required attributes={}".format(
                    mode, REQUIRED_ATTRIBUTES.get(mode)
                )
                log.warning(msg)
                raise EnrollmentAttributesMissingError(msg)

            response = api.update_enrollment(
                username,
                str(course_id),
                mode=mode,
                is_active=is_active,
                enrollment_attributes=enrollment_attributes,
                # If we are updating enrollment by authorized api caller, we should allow expired modes
                include_expired=has_api_key_permissions
            )
        else:
            # Will reactivate inactive enrollments.
            response = api.add_enrollment(
                username,
                str(course_id),
                mode=mode,
                is_active=is_active,
                enrollment_attributes=enrollment_attributes
            )

        if cohort_name is not None:
            cohort = get_cohort_by_name(course_id, cohort_name)
            try:
                add_user_to_cohort(cohort, user)
            except ValueError:
                # user already in cohort, probably because they were un-enrolled and re-enrolled
                log.exception('Cohort re-addition')

        log.info('The user [%s] has already been enrolled in course run [%s].', username, course_id)
        return response
    except CourseEnrollmentExistsError as error:
        log.warning('An enrollment already exists for user [%s] in course run [%s].', username, course_id)
        raise(error)
    except CourseEnrollmentError as error:
        log.exception("An error occurred while creating the new course enrollment for user "
                      "[%s] in course run [%s]", username, course_id)
        raise(error)
    except CourseUserGroup.DoesNotExist as error:
        log.exception('Missing cohort [%s] in course run [%s]', cohort_name, course_id)
        raise(error)
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
