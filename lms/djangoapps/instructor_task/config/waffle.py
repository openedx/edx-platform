"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""
from __future__ import absolute_import

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace


INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'instructor_task')

# Course-specific flags
PROBLEM_GRADE_REPORT_VERIFIED_ONLY = u'problem_grade_report_verified_only'


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
    }


def problem_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return waffle_flags()[PROBLEM_GRADE_REPORT_VERIFIED_ONLY].is_enabled(course_id)
