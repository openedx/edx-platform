"""
Provides Python APIs exposed from Student models.
"""

from student.models import CourseEnrollment as _CourseEnrollment
from student.models import ManualEnrollmentAudit as _ManualEnrollmentAudit
from student.models import (
    ENROLLED_TO_ENROLLED as _ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED as _ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED as _UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED as _UNENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL as _UNENROLLED_TO_ALLOWEDTOENROLL,
    ALLOWEDTOENROLL_TO_ENROLLED as _ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED as _ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE as _DEFAULT_TRANSITION_STATE,
)

# This is done so that if these strings change within the app, we can keep exported constants the same
ENROLLED_TO_ENROLLED = _ENROLLED_TO_ENROLLED
ENROLLED_TO_UNENROLLED = _ENROLLED_TO_UNENROLLED
UNENROLLED_TO_ENROLLED = _UNENROLLED_TO_ENROLLED
UNENROLLED_TO_UNENROLLED = _UNENROLLED_TO_UNENROLLED
UNENROLLED_TO_ALLOWEDTOENROLL = _UNENROLLED_TO_ALLOWEDTOENROLL
ALLOWEDTOENROLL_TO_ENROLLED = _ALLOWEDTOENROLL_TO_ENROLLED
ALLOWEDTOENROLL_TO_UNENROLLED = _ALLOWEDTOENROLL_TO_UNENROLLED
DEFAULT_TRANSITION_STATE = _DEFAULT_TRANSITION_STATE


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
