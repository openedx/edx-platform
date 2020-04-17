"""
Provides Python APIs exposed from Student models.
"""
import logging

from django.apps import apps
from django.conf import settings
from user_util import user_util

from django.contrib.auth.models import User as _User
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
from student.models import UserProfile as _UserProfile

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


def is_username_retired(username):
    """
    Checks to see if the given username has been previously retired
    """
    locally_hashed_usernames = user_util.get_all_retired_usernames(
        username,
        settings.RETIRED_USER_SALTS,
        settings.RETIRED_USERNAME_FMT
    )

    # TODO: Revert to this after username capitalization issues detailed in
    # PLAT-2276, PLAT-2277, PLAT-2278 are sorted out:
    # return User.objects.filter(username__in=list(locally_hashed_usernames)).exists()

    # Avoid circular import issues
    from openedx.core.djangoapps.user_api.models import UserRetirementStatus

    # Sandbox clean builds attempt to create users during migrations, before the database
    # is stable so UserRetirementStatus may not exist yet. This workaround can also go
    # when we are done with the username updates.
    try:
        return _User.objects.filter(username__in=list(locally_hashed_usernames)).exists() or \
            UserRetirementStatus.objects.filter(original_username=username).exists()
    except ProgrammingError as exc:
        # Check the error message to make sure it's what we expect
        if "user_api_userretirementstatus" in text_type(exc):
            return User.objects.filter(username__in=list(locally_hashed_usernames)).exists()
        raise


def is_email_retired(email):
    """
    Checks to see if the given email has been previously retired
    """
    locally_hashed_emails = user_util.get_all_retired_emails(
        email,
        settings.RETIRED_USER_SALTS,
        settings.RETIRED_EMAIL_FMT
    )

    return _User.objects.filter(email__in=list(locally_hashed_emails)).exists()

def get_user_last_login_by_username(username):
    """
    Get the user's last login by the username. If the user specified by username does not exist,
    return None.
    
    Note that last login refers to the last time the user authenticated with edX. 
    It does not refer to the last time a user visited edX.

    Arguments:
        username: the username of the user
    """
    try:
        return _User.objects.get(username=username).last_login
    except _User.DoesNotExist:
        return None

def get_user_retirement_date(user):
    """
    Get the date on which the user completed retirement (i.e. the modified time of a UserRetirementStatus record with the COMPLETE state). 
    If there does not exist a UserRetirementStatus record with the COMPLETE state for the user, return None.

    Arguments:
        user: the user who retirement date we want
    """
    UserRetirementStatus = apps.get_model('user_api', 'UserRetirementStatus')
    try:
        return UserRetirementStatus.objects.get(user=user, current_state__state_name='COMPLETE').modified
    except UserRetirementStatus.DoesNotExist:
        return None
