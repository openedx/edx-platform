    # pylint: disable=unused-import
"""
Python APIs exposed by the student app to other in-process apps.
"""
import datetime
import logging

from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from common.djangoapps.student.models import CourseEnrollment as _CourseEnrollment, UserProfile as _UserProfile, \
    CourseAccessRole as _CourseAccessRole, PendingNameChange as _PendingNameChange, \
    ManualEnrollmentAudit as _ManualEnrollmentAudit
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
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
    REGISTERED_ACCESS_ROLES as _REGISTERED_ACCESS_ROLES,
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

COURSE_DASHBOARD_PLUGIN_VIEW_NAME = "course_dashboard"

log = logging.getLogger()


def _create_manual_enrollment_audit(
    enrolled_by,
    user_email,
    state_transition,
    reason,
    course_enrollment
):
    """
    Creates a record of a student being manually enrolled in a course via the ManualEnrollmentAudit
    model.  The corresponding StudentEnrollment is not created by this function.
    @param enrolled_by:
    @param user_email:
    @param state_transition:
    @param reason:
    @param course_enrollment:
    """
    _ManualEnrollmentAudit.create_manual_enrollment_audit(
        user=enrolled_by,
        email=user_email,
        state_transition=state_transition,
        reason=reason,
        enrollment=course_enrollment,
    )


def get_course_enrollment(user, course_run_key):
    return _CourseEnrollment.get_enrollment(user, course_run_key)


def create_manual_enrollment_audit(
    enrolled_by,
    user_email,
    transition_state,
    reason,
    course_run_key=None,
):
    """
    Creates an audit item for a manual enrollment.
    Parameters:
        enrolled_by: <auth.User> of the person that is manually enrolling
        user_email: <str> email of the user being enrolled
        transition_state: <str> state of enrollment transition state from _TRANSITIONS_STATES
        reason: <str> Reason why user was manually enrolled
        course_run_key: <str> Used to link the audit enrollment to the actual enrollment

    Note: We purposefully *exclude* passing items like CourseEnrollment objects to prevent callers from needed to
    know about model level code.
    """
    if transition_state not in TRANSITION_STATES:
        raise ValueError(f"State `{transition_state}` not in allow states: `{TRANSITION_STATES}`")

    User = get_user_model()
    try:
        enrolled_user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        enrolled_user = None

    if enrolled_user and course_run_key:
        enrollment = get_course_enrollment(enrolled_user, course_run_key)
    else:
        enrollment = None

    _create_manual_enrollment_audit(
        enrolled_by,
        user_email,
        transition_state,
        reason,
        enrollment
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


def is_user_enrolled_in_course(student, course_key):
    """
    Determines if a learner is enrolled in a given course-run.
    """
    log.info(f"Checking if {student.id} is enrolled in course {course_key}")
    return _CourseEnrollment.is_enrolled(student, course_key)


def is_user_staff_or_instructor_in_course(user, course_key):
    """
    Determines if a user is an Instructor or part of the given course's course staff.

    Also returns true for GlobalStaff.
    """
    if not isinstance(course_key, CourseKey):
        course_key = CourseKey.from_string(course_key)

    return (
        GlobalStaff().has_user(user) or
        CourseStaffRole(course_key).has_user(user) or
        CourseInstructorRole(course_key).has_user(user)
    )


def get_phone_number(user_id):
    """
    Get a user's phone number from the profile, if
    one exists. Otherwise, return None.
    """
    try:
        student = _UserProfile.objects.get(user_id=user_id)
    except _UserProfile.DoesNotExist as exception:
        log.exception(exception)
        return None
    return student.phone_number or None


def get_name(user_id):
    """
    Get a user's name from their profile, if one exists. Otherwise, return None.
    """
    try:
        student = _UserProfile.objects.get(user_id=user_id)
    except _UserProfile.DoesNotExist:
        log.exception(f'Could not find UserProfile for id {user_id}')
        return None
    return student.name or None


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


def get_pending_name_change(user):
    """
    Return the user's pending name change, or None if it does not exist.
    """
    try:
        pending_name_change = _PendingNameChange.objects.get(user=user)
        return pending_name_change
    except _PendingNameChange.DoesNotExist:
        return None


def do_name_change_request(user, new_name, rationale):
    """
    Create a name change request. This either updates the user's current PendingNameChange, or creates
    a new one if it doesn't exist. Returns the PendingNameChange object and a boolean describing whether
    or not a new one was created.
    """
    user_profile = _UserProfile.objects.get(user=user)
    if user_profile.name == new_name:
        log_msg = (
            'user_id={user_id} requested a name change, but the requested name is the same as'
            'their current profile name. Not taking any action.'.format(user_id=user.id)
        )
        log.warning(log_msg)
        return None, False

    pending_name_change, created = _PendingNameChange.objects.update_or_create(
        user=user,
        defaults={
            'new_name': new_name,
            'rationale': rationale
        }
    )

    return pending_name_change, created


def confirm_name_change(user, pending_name_change):
    """
    Confirm a pending name change. This updates the user's profile name and deletes the
    PendingNameChange object.
    """
    user_profile = _UserProfile.objects.get(user=user)

    # Store old name in profile metadata
    meta = user_profile.get_meta()
    if 'old_names' not in meta:
        meta['old_names'] = []
    meta['old_names'].append(
        [user_profile.name, pending_name_change.rationale, datetime.datetime.now(UTC).isoformat()]
    )
    user_profile.set_meta(meta)

    user_profile.name = pending_name_change.new_name
    user_profile.save()
    pending_name_change.delete()
