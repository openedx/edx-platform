"""
Toggles for course apps.
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

#: Namespace for use by course apps for creating availability toggles
COURSE_APPS_WAFFLE_NAMESPACE = 'course_apps'

# .. toggle_name: course_apps.proctoring_settings_modal_view
# .. toggle_use_cases: temporary
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, users will be directed to a new proctoring settings
#    modal on the Pages and Resources view when accessing proctored exam settings.
# .. toggle_warning: None
# .. toggle_creation_date: 2021-08-17
# .. toggle_target_removal_date: None
PROCTORING_SETTINGS_MODAL_VIEW = CourseWaffleFlag(
    f'{COURSE_APPS_WAFFLE_NAMESPACE}.proctoring_settings_modal_view', __name__
)

# .. toggle_name: course_apps.exams_ida
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Uses exams IDA
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-07-27
# .. toggle_target_removal_date: None
# .. toggle_tickets: MST-1520
EXAMS_IDA = CourseWaffleFlag(
    f'{COURSE_APPS_WAFFLE_NAMESPACE}.exams_ida', __name__
)


def proctoring_settings_modal_view_enabled(course_key):
    """
    Returns a boolean if proctoring settings modal view is enabled for a course.
    """
    return PROCTORING_SETTINGS_MODAL_VIEW.is_enabled(course_key)


def exams_ida_enabled(course_key):
    """
    Returns a boolean if exams ida view is enabled for a course.
    """
    return EXAMS_IDA.is_enabled(course_key)
