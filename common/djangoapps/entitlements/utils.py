from course_modes.models import CourseMode
from django.utils import timezone

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def is_course_run_entitlement_fullfillable(course_run_id, entitlement, compare_date=timezone.now()):
    """
    Checks that the current run meets the following criteria for an entitlement

    1) Is currently running or start in the future
    2) A User can enroll in
    3) A User can upgrade to the entitlement mode

    Arguments:
        course_run_id (String): The id of the Course run that is being checked.
        entitlement: The Entitlement that we are checking against.
        compare_date: The date and time that we are comparing against.  Defaults to timezone.now()

    Returns:
        bool: True if the Course Run is fullfillable for the CourseEntitlement.
    """
    course_overview = CourseOverview.get_from_id(course_run_id)

    # Verify that the course is still running
    run_start = course_overview.start
    run_end = course_overview.end
    is_running = run_start and (not run_end or (run_end and (run_end > compare_date)))

    # Verify that the course run can currently be enrolled
    enrollment_start = course_overview.enrollment_start
    enrollment_end = course_overview.enrollment_end
    can_enroll = (
        (not enrollment_start or enrollment_start < compare_date)
        and (not enrollment_end or enrollment_end > compare_date)
    )

    # Ensure the course run is upgradeable and the mode matches the entitlement's mode
    unexpired_paid_modes = [mode.slug for mode in CourseMode.paid_modes_for_course(course_run_id)]
    can_upgrade = unexpired_paid_modes and entitlement.mode in unexpired_paid_modes

    return is_running and can_upgrade and can_enroll
