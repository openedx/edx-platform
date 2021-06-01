"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""


from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, WaffleSwitchNamespace

WAFFLE_NAMESPACE = u'instructor_task'
INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=WAFFLE_NAMESPACE)
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switches
OPTIMIZE_GET_LEARNERS_FOR_COURSE = u'optimize_get_learners_for_course'
GENERATE_GRADE_REPORT_VERIFIED_ONLY = u'generate_grade_report_for_verified_only'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    return {}


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return WAFFLE_SWITCHES.is_enabled(OPTIMIZE_GET_LEARNERS_FOR_COURSE)


def generate_grade_report_for_verified_only():
    """
    Returns True if waffle switch is enabled that indicates generate grading reports only for
    verified learners.
    """
    return WAFFLE_SWITCHES.is_enabled(GENERATE_GRADE_REPORT_VERIFIED_ONLY)
