"""
Provides Python APIs exposed from Student models.
"""
import logging

from common.djangoapps.student.models import CourseAccessRole as _CourseAccessRole
from common.djangoapps.student.models import CourseEnrollment as _CourseEnrollment
from common.djangoapps.student.models import ManualEnrollmentAudit as _ManualEnrollmentAudit
from common.djangoapps.student.models import (
    ENROLLED_TO_ENROLLED as _ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED as _ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED as _UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED as _UNENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL as _UNENROLLED_TO_ALLOWEDTOENROLL,
    ALLOWEDTOENROLL_TO_ENROLLED as _ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED as _ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE as _DEFAULT_TRANSITION_STATE,
)
from common.djangoapps.student.models import UserProfile as _UserProfile

# This is done so that if these strings change within the app, we can keep exported constants the same
ENROLLED_TO_ENROLLED = _ENROLLED_TO_ENROLLED
ENROLLED_TO_UNENROLLED = _ENROLLED_TO_UNENROLLED
UNENROLLED_TO_ENROLLED = _UNENROLLED_TO_ENROLLED
UNENROLLED_TO_UNENROLLED = _UNENROLLED_TO_UNENROLLED
UNENROLLED_TO_ALLOWEDTOENROLL = _UNENROLLED_TO_ALLOWEDTOENROLL
ALLOWEDTOENROLL_TO_ENROLLED = _ALLOWEDTOENROLL_TO_ENROLLED
ALLOWEDTOENROLL_TO_UNENROLLED = _ALLOWEDTOENROLL_TO_UNENROLLED
DEFAULT_TRANSITION_STATE = _DEFAULT_TRANSITION_STATE
log = logging.getLogger(__name__)


def create_manual_enrollment_audit(
    enrolled_by,
    user_email,
    state_transition,
    reason,
    course_enrollment,
    role
):
    _ManualEnrollmentAudit.create_manual_enrollment_audit(
        user=enrolled_by,
        email=user_email,
        state_transition=state_transition,
        reason=reason,
        enrollment=course_enrollment,
        role=role,
    )


def get_course_enrollment(user, course_run_key):
    return _CourseEnrollment.get_enrollment(user, course_run_key)


def get_phone_number(user_id):
    """
    Get a users phone number from the profile, if
    one exists. Otherwise, return None.
    """
    try:
        student = _UserProfile.objects.get(user_id=user_id)
    except _UserProfile.DoesNotExist as exception:
        log.exception(exception)
        return None
    return student.phone_number or None


def get_course_access_role(user, org, course_id, role):
    """
    Get a specific CourseAccessRole object. Return None if
    it does not exist.

    Arguments:
        user: User object for the user who has access in a course
        org: the org the course is in
        course_id: the course_id of the CourseAccessRole
        role: the role type of the role
    """
    try:
        course_access_role = _CourseAccessRole.objects.get(
            user=user,
            org=org,
            course_id=course_id,
            role=role,
        )
    except _CourseAccessRole.DoesNotExist:
        log.exception('No CourseAccessRole found for user_id=%(user_id)s, org=%(org)s, '
                      'course_id=%(course_id)s, and role=%(role)s.', {
                          'user': user.id,
                          'org': org,
                          'course_id': course_id,
                          'role': role,
                      })
        return None
    return course_access_role
