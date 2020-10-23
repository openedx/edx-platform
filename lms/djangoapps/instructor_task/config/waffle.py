"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""

from edx_toggles.toggles import WaffleFlagNamespace, WaffleSwitchNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'instructor_task'
INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=WAFFLE_NAMESPACE)
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switches
OPTIMIZE_GET_LEARNERS_FOR_COURSE = 'optimize_get_learners_for_course'

# Course override flags
GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY = 'generate_problem_grade_report_verified_only'
GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY = 'generate_course_grade_report_verified_only'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    return {
        GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY: CourseWaffleFlag(
            waffle_namespace=INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE,
            flag_name=GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY,
            module_name=__name__,
        ),
        GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY: CourseWaffleFlag(
            waffle_namespace=INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE,
            flag_name=GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY,
            module_name=__name__,
        ),
    }


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return WAFFLE_SWITCHES.is_enabled(OPTIMIZE_GET_LEARNERS_FOR_COURSE)


def problem_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return waffle_flags()[GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY].is_enabled(course_id)


def course_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return waffle_flags()[GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY].is_enabled(course_id)
