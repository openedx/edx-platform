"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""


from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

WAFFLE_NAMESPACE = u'instructor_task'
INSTRUCTOR_TASK_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=WAFFLE_NAMESPACE)
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switches
OPTIMIZE_GET_LEARNERS_FOR_COURSE = u'optimize_get_learners_for_course'
DATA_DOWNLOAD_REPORTS_NEW_UI = 'data_download_reports_new_ui'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='Instructor Task: ')
    return {
        DATA_DOWNLOAD_REPORTS_NEW_UI: CourseWaffleFlag(
            namespace,
            DATA_DOWNLOAD_REPORTS_NEW_UI,
            flag_undefined_default=True,
        ),
    }


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return WAFFLE_SWITCHES.is_enabled(OPTIMIZE_GET_LEARNERS_FOR_COURSE)


def new_ui_for_data_download_csv_reports(course_key):
    """
    Returns whether new UI is enabled for CSV reports in instructor dashboard for a given course.
    """
    return waffle_flags()[DATA_DOWNLOAD_REPORTS_NEW_UI].is_enabled(course_key)
