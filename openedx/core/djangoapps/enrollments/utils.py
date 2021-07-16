"""
Utils for use in enrollment code
"""
import logging
from openedx.core.djangoapps.enrollments.errors import EnrollmentModeMismatchError, EnrollmentAttributesMissingError
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort, get_cohort_by_name
from openedx.core.djangoapps.enrollments import api

logger = logging.getLogger(__name__)

REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}


def add_user_to_course_cohort(cohort_name, course_id, user):
    if cohort_name is not None:
        cohort = get_cohort_by_name(course_id, cohort_name)
        try:
            add_user_to_cohort(cohort, user)
        except ValueError:
            # user already in cohort, probably because they were un-enrolled and re-enrolled
            logger.exception('Cohort re-addition')


def check_mode_and_enroll(username, course_id, mode, enrollment, enrollment_attributes, is_active, has_api_key_permissions):
    """
    Checks if a mode change is being attempted, and updates or adds an enrollment.
    Raises:
     - EnrollmentModeMismatchError or EnrollmentAttributesMissingError
    """
    mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
    active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
    missing_attrs = []
    if enrollment_attributes:
        actual_attrs = [
            "{namespace}:{name}".format(**attr)
            for attr in enrollment_attributes
        ]
        missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
    if mode_changed or active_changed:
        if mode_changed and active_changed and not is_active:
            # if the requester wanted to deactivate but specified the wrong mode, fail
            # the request (on the assumption that the requester had outdated information
            # about the currently active enrollment).
            msg = "Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                enrollment["mode"], mode
            )
            logger.warning(msg)
            raise EnrollmentModeMismatchError(msg)

        if missing_attrs:
            msg = "Missing enrollment attributes: requested mode={} required attributes={}".format(
                mode, REQUIRED_ATTRIBUTES.get(mode)
            )
            logger.warning(msg)
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
    return response
