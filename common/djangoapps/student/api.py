# pylint: disable=unused-import
"""
Python APIs exposed by the student app to other in-process apps.
"""


from django.contrib.auth import get_user_model
from django.conf import settings

from common.djangoapps.student.models_api import create_manual_enrollment_audit as _create_manual_enrollment_audit
from common.djangoapps.student.models_api import get_course_access_role
from common.djangoapps.student.models_api import get_course_enrollment as _get_course_enrollment
from common.djangoapps.student.models_api import (
    ENROLLED_TO_ENROLLED as _ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED as _ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED as _UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED as _UNENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL as _UNENROLLED_TO_ALLOWEDTOENROLL,
    ALLOWEDTOENROLL_TO_ENROLLED as _ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED as _ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE as _DEFAULT_TRANSITION_STATE,
)
from common.djangoapps.student.roles import REGISTERED_ACCESS_ROLES as _REGISTERED_ACCESS_ROLES
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

COURSE_DASHBOARD_PLUGIN_VIEW_NAME = "course_dashboard"


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


def get_access_role_by_role_name(role_name):
    """
    Get the concrete child class of the AccessRole abstract class associated with the string role_name
    by looking in REGISTERED_ACCESS_ROLES. If there is no class associated with this name, return None.

    Note that this will only return classes that are registered in _REGISTERED_ACCESS_ROLES.

    Arguments:
        role_name: the name of the role
    """
    return _REGISTERED_ACCESS_ROLES.get(role_name, None)
