"""
Simple utility functions for computing access.
It allows us to share code between access.py and block transformers.
"""


from datetime import datetime, timedelta
from logging import getLogger

from crum import get_current_request
from django.conf import settings
from enterprise.models import EnterpriseCourseEnrollment, EnterpriseCustomerUser
from pytz import UTC

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseBetaTesterRole
from lms.djangoapps.courseware.access_response import (
    AccessResponse,
    AuthenticationRequiredAccessError,
    DataSharingConsentRequiredAccessError,
    EnrollmentRequiredAccessError,
    IncorrectActiveEnterpriseAccessError,
    StartDateError
)
from lms.djangoapps.courseware.masquerade import get_course_masquerade, is_masquerading_as_student
from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, COURSE_PRE_START_ACCESS_FLAG
from xmodule.course_block import COURSE_VISIBILITY_PUBLIC  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.util.xmodule_django import get_current_request_hostname  # lint-amnesty, pylint: disable=wrong-import-order

DEBUG_ACCESS = False
log = getLogger(__name__)

ACCESS_GRANTED = AccessResponse(True)
ACCESS_DENIED = AccessResponse(False)


def debug(*args, **kwargs):
    """
    Helper function for local debugging.
    """
    # to avoid overly verbose output, this is off by default
    if DEBUG_ACCESS:
        log.debug(*args, **kwargs)


def adjust_start_date(user, days_early_for_beta, start, course_key):
    """
    If user is in a beta test group, adjust the start date by the appropriate number of
    days.

    Returns:
        A datetime.  Either the same as start, or earlier for beta testers.
    """
    if days_early_for_beta is None:
        # bail early if no beta testing is set up
        return start

    if CourseBetaTesterRole(course_key).has_user(user):
        debug("Adjust start time: user in beta role for %s", course_key)
        delta = timedelta(days_early_for_beta)
        effective = start - delta
        return effective

    return start


def check_start_date(user, days_early_for_beta, start, course_key, display_error_to_user=True, now=None):
    """
    Verifies whether the given user is allowed access given the
    start date and the Beta offset for the given course.

    Arguments:
        display_error_to_user: If True, display this error to users in the UI.

    Returns:
        AccessResponse: Either ACCESS_GRANTED or StartDateError.
    """
    start_dates_disabled = settings.FEATURES['DISABLE_START_DATES']
    masquerading_as_student = is_masquerading_as_student(user, course_key)

    if start_dates_disabled and not masquerading_as_student:
        return ACCESS_GRANTED
    else:
        if start is None or in_preview_mode() or get_course_masquerade(user, course_key):
            return ACCESS_GRANTED

        if now is None:
            now = datetime.now(UTC)
        effective_start = adjust_start_date(user, days_early_for_beta, start, course_key)

        should_grant_access = now > effective_start
        if should_grant_access:
            return ACCESS_GRANTED

        return StartDateError(start, display_error_to_user=display_error_to_user)


def in_preview_mode():
    """
    Returns whether the user is in preview mode or not.
    """
    hostname = get_current_request_hostname()
    preview_lms_base = settings.FEATURES.get('PREVIEW_LMS_BASE', None)
    return bool(preview_lms_base and hostname and hostname.split(':')[0] == preview_lms_base.split(':')[0])


def check_course_open_for_learner(user, course):
    """
    Check if the course is open for learners based on the start date.

    Returns:
        AccessResponse: Either ACCESS_GRANTED or StartDateError.
    """
    if COURSE_PRE_START_ACCESS_FLAG.is_enabled():
        return ACCESS_GRANTED
    return check_start_date(user, course.days_early_for_beta, course.start, course.id)


def check_enrollment(user, course):
    """
    Check if the course requires a learner to be enrolled for access.

    Returns:
        AccessResponse: Either ACCESS_GRANTED or EnrollmentRequiredAccessError.
    """
    if check_public_access(course, [COURSE_VISIBILITY_PUBLIC]):
        return ACCESS_GRANTED

    if CourseEnrollment.is_enrolled(user, course.id):
        return ACCESS_GRANTED

    return EnrollmentRequiredAccessError()


def check_authentication(user, course):
    """
    Grants access if the user is authenticated, or if the course allows public access.

    Returns:
        AccessResponse: Either ACCESS_GRANTED or AuthenticationRequiredAccessError
    """
    if user.is_authenticated:
        return ACCESS_GRANTED

    if check_public_access(course, [COURSE_VISIBILITY_PUBLIC]):
        return ACCESS_GRANTED

    return AuthenticationRequiredAccessError()


def check_public_access(course, visibilities):
    """
    This checks if the unenrolled access waffle flag for the course is set
    and the course visibility matches any of the input visibilities.

    The "visibilities" argument is one of these constants from xmodule.course_block:
    - COURSE_VISIBILITY_PRIVATE
    - COURSE_VISIBILITY_PUBLIC
    - COURSE_VISIBILITY_PUBLIC_OUTLINE

    Returns:
        AccessResponse: Either ACCESS_GRANTED or ACCESS_DENIED.
    """

    unenrolled_access_flag = COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.is_enabled(course.id)
    allow_access = unenrolled_access_flag and course.course_visibility in visibilities
    if allow_access:
        return ACCESS_GRANTED

    return ACCESS_DENIED


def check_data_sharing_consent(course_id):
    """
        Grants access if the user is do not need DataSharing consent, otherwise returns data sharing link.

        Returns:
            AccessResponse: Either ACCESS_GRANTED or DataSharingConsentRequiredAccessError
        """
    from openedx.features.enterprise_support.api import get_enterprise_consent_url
    consent_url = get_enterprise_consent_url(
        request=get_current_request(),
        course_id=str(course_id),
        return_to='courseware',
        enrollment_exists=True,
        source='CoursewareAccess'
    )
    if consent_url:
        return DataSharingConsentRequiredAccessError(consent_url=consent_url)
    return ACCESS_GRANTED


def check_correct_active_enterprise_customer(user, course_id):
    """
    Grants access if the user's active enterprise customer is same as  EnterpriseCourseEnrollment's Enterprise.
    Also, Grant access if enrollment is not Enterprise

    Returns:
        AccessResponse: Either ACCESS_GRANTED or IncorrectActiveEnterpriseAccessError
    """
    enterprise_enrollments = EnterpriseCourseEnrollment.objects.filter(
        course_id=course_id, enterprise_customer_user__user_id=user.id
    )
    if not enterprise_enrollments.exists():
        return ACCESS_GRANTED

    try:
        active_enterprise_customer_user = EnterpriseCustomerUser.objects.get(user_id=user.id, active=True)
        if enterprise_enrollments.filter(enterprise_customer_user=active_enterprise_customer_user).exists():
            return ACCESS_GRANTED

        active_enterprise_name = active_enterprise_customer_user.enterprise_customer.name
    except (EnterpriseCustomerUser.DoesNotExist, EnterpriseCustomerUser.MultipleObjectsReturned):
        # Ideally this should not happen. As there should be only 1 active enterprise customer in our system
        log.error("Multiple or No Active Enterprise found for the user %s.", user.id)
        active_enterprise_name = 'Incorrect'

    enrollment_enterprise_name = enterprise_enrollments.first().enterprise_customer_user.enterprise_customer.name
    return IncorrectActiveEnterpriseAccessError(enrollment_enterprise_name, active_enterprise_name)


def is_priority_access_error(access_error):
    """
    Check if given access error is a priority Access Error or not.
    Priority Access Error can not be bypassed by staff users.
    """
    priority_access_errors = [
        DataSharingConsentRequiredAccessError,
        IncorrectActiveEnterpriseAccessError,
    ]
    for priority_access_error in priority_access_errors:
        if isinstance(access_error, priority_access_error):
            return True
    return False
