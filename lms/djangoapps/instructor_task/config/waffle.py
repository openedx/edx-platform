"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""
from __future__ import absolute_import

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

WAFFLE_NAMESPACE = u'instructor_task'
INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=WAFFLE_NAMESPACE)
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switches
OPTIMIZE_GET_LEARNERS_FOR_COURSE = u'optimize_get_learners_for_course'

# Course-specific flags
PROBLEM_GRADE_REPORT_VERIFIED_ONLY = u'problem_grade_report_verified_only'
COURSE_GRADE_REPORT_VERIFIED_ONLY = u'course_grade_report_verified_only'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    return {
        PROBLEM_GRADE_REPORT_VERIFIED_ONLY: CourseWaffleFlag(
            waffle_namespace=INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE,
            flag_name=PROBLEM_GRADE_REPORT_VERIFIED_ONLY,
            flag_undefined_default=False,
        ),
        COURSE_GRADE_REPORT_VERIFIED_ONLY: CourseWaffleFlag(
            waffle_namespace=INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE,
            flag_name=COURSE_GRADE_REPORT_VERIFIED_ONLY,
            flag_undefined_default=False,
        ),
    }


def problem_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return waffle_flags()[PROBLEM_GRADE_REPORT_VERIFIED_ONLY].is_enabled(course_id)


def course_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return waffle_flags()[PROBLEM_GRADE_REPORT_VERIFIED_ONLY].is_enabled(course_id)


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return WAFFLE_SWITCHES.is_enabled(OPTIMIZE_GET_LEARNERS_FOR_COURSE)
