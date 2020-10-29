"""
Utility methods for the entitlement application.
"""


import logging

from django.utils import timezone

from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment

log = logging.getLogger("common.entitlements.utils")


def is_course_run_entitlement_fulfillable(
        course_run_key,
        entitlement,
        compare_date=timezone.now(),
):
    """
    Checks that the current run meets the following criteria for an entitlement

    1) A User can enroll in or is currently enrolled
    2) A User can upgrade to the entitlement mode

    Arguments:
        course_run_key (CourseKey): The id of the Course run that is being checked.
        entitlement: The Entitlement that we are checking against.
        compare_date: The date and time that we are comparing against.  Defaults to timezone.now()

    Returns:
        bool: True if the Course Run is fullfillable for the CourseEntitlement.
    """
    try:
        course_overview = CourseOverview.get_from_id(course_run_key)
    except CourseOverview.DoesNotExist:
        log.error((u'There is no CourseOverview entry available for {course_run_id}, '
                   u'course run cannot be applied to entitlement').format(
            course_run_id=str(course_run_key)
        ))
        return False

    # Verify that the course run can currently be enrolled
    enrollment_start = course_overview.enrollment_start
    enrollment_end = course_overview.enrollment_end
    can_enroll = (
        (not enrollment_start or enrollment_start < compare_date)
        and (not enrollment_end or enrollment_end > compare_date)
    )

    # Is the user already enrolled in the Course Run
    is_enrolled = CourseEnrollment.is_enrolled(entitlement.user, course_run_key)

    # Ensure the course run is upgradeable and the mode matches the entitlement's mode
    unexpired_paid_modes = [mode.slug for mode in CourseMode.paid_modes_for_course(course_run_key)]
    can_upgrade = unexpired_paid_modes and entitlement.mode in unexpired_paid_modes

    return course_overview.start and can_upgrade and (is_enrolled or can_enroll)
