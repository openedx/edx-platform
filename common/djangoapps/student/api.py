from django.contrib.auth import get_user_model
from django.conf import settings

from student.models_api import create_manual_enrollment_audit as _create_manual_enrollment_audit
from student.models_api import get_course_enrollment as _get_course_enrollment
from student.models_api import (
    ENROLLED_TO_ENROLLED as _ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED as _ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED as _UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED as _UNENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL as _UNENROLLED_TO_ALLOWEDTOENROLL,
    ALLOWEDTOENROLL_TO_ENROLLED as _ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED as _ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE as _DEFAULT_TRANSITION_STATE,
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


# This is done so that if these strings change within the app, we can keep exported constants the same
ENROLLED_TO_ENROLLED = _ENROLLED_TO_ENROLLED
ENROLLED_TO_UNENROLLED = _ENROLLED_TO_UNENROLLED
UNENROLLED_TO_ENROLLED = _UNENROLLED_TO_ENROLLED
UNENROLLED_TO_UNENROLLED = _UNENROLLED_TO_UNENROLLED
UNENROLLED_TO_ALLOWEDTOENROLL = _UNENROLLED_TO_ALLOWEDTOENROLL
ALLOWEDTOENROLL_TO_ENROLLED = _ALLOWEDTOENROLL_TO_ENROLLED
ALLOWEDTOENROLL_TO_UNENROLLED = _ALLOWEDTOENROLL_TO_UNENROLLED
DEFAULT_TRANSITION_STATE = _DEFAULT_TRANSITION_STATE

TRANSITION_STATES = (
    ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE,
)

MANUAL_ENROLLMENT_ROLE_CHOICES = configuration_helpers.get_value(
    'MANUAL_ENROLLMENT_ROLE_CHOICES',
    settings.MANUAL_ENROLLMENT_ROLE_CHOICES
)


def create_manual_enrollment_audit(
    enrolled_by,
    user_email,
    transition_state,
    reason,
    course_run_key=None,
    role=None
):
    """
    Creates an audit item for a manual enrollment.
    Parameters:
        enrolled_by: <auth.User> of the person that is manually enrolling
        user_email: <str> email of the user being enrolled
        transition_state: <str> state of enrollment transition state from _TRANSITIONS_STATES
        reason: <str> Reason why user was manually enrolled
        course_run_key: <str> Used to link the audit enrollment to the actual enrollment
        role: <str> role of the enrolled user from MANUAL_ENROLLMENT_ROLE_CHOICES

    Note: We purposefully *exclude* passing items like CourseEnrollment objects to prevent callers from needed to
    know about model level code.
    """
    if role and role not in MANUAL_ENROLLMENT_ROLE_CHOICES:
        raise ValueError("Role `{}` not in allowed roles: `{}".format(role, MANUAL_ENROLLMENT_ROLE_CHOICES))
    if transition_state not in TRANSITION_STATES:
        raise ValueError("State `{}` not in allow states: `{}`".format(transition_state, TRANSITION_STATES))

    User = get_user_model()
    try:
        enrolled_user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        enrolled_user = None

    if enrolled_user and course_run_key:
        enrollment = _get_course_enrollment(enrolled_user, course_run_key)
    else:
        enrollment = None

    _create_manual_enrollment_audit(
        enrolled_by,
        user_email,
        transition_state,
        reason,
        enrollment,
        role
    )
