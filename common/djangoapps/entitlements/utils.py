from course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment


def is_course_run_entitlement_fullfillable(course_run_id, compare_date, entitlement):
    """
    Checks that the current run meets the following criteria for an entitlement

    1) Are currently running or start in the future
    2) A user can enroll in
    3) A user can upgrade to the entitlement mode
    4) Are not already currently enrolled in a session

    Arguments:
        course_run_id (String): The id of the Course run that is being checked.
        compare_date: The date and time that we are comparing against.  Generally the current date and time.
        user_enrolled_sessions (list): The list of sessions that the user is enrolled in currently.
        mode (String): The current mode of the entitlement that we are verifying against.

    Returns:
        bool: True is the Course Run is fullfillable for the CourseEntitlement.
    """
    # Only courses that have not ended will be displayed
    course_overview = CourseOverview.get_from_id(course_run_id)

    run_start = course_overview.start
    run_end = course_overview.end
    is_running = run_start and (not run_end or (run_end and (run_end > compare_date)))

    # Only courses that can currently be enrolled in will be displayed
    enrollment_start = course_overview.enrollment_start
    enrollment_end = course_overview.enrollment_end
    is_enrolled = CourseEnrollment.is_enrolled(entitlement.user, course_run_id)
    can_enroll = (
        (not enrollment_start or enrollment_start < compare_date)
        and (not enrollment_end or enrollment_end > compare_date)
        and not is_enrolled
    )

    # Check if it is an upgradable mode and mode matches entitlement mode
    can_upgrade = False
    unexpired_paid_modes = [mode.slug for mode in CourseMode.paid_modes_for_course(course_run_id)]
    if unexpired_paid_modes and entitlement.mode in unexpired_paid_modes:
        can_upgrade = True

    return is_running and can_upgrade and can_enroll
