"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""

from edx_toggles.toggles import WaffleSwitch

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_NAMESPACE = 'instructor_task'

# Waffle switches
OPTIMIZE_GET_LEARNERS_FOR_COURSE = WaffleSwitch(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.optimize_get_learners_for_course', __name__
)

# Course override flags
GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.generate_problem_grade_report_verified_only', __name__
)

GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.generate_course_grade_report_verified_only', __name__
)


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return OPTIMIZE_GET_LEARNERS_FOR_COURSE.is_enabled()


def problem_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY.is_enabled(course_id)


def course_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY.is_enabled(course_id)
