"""
The utility methods and functions to help the djangoapp logic
"""

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.learner_dashboard.config.waffle import ENABLE_PROGRAM_TAB_VIEW, ENABLE_MASTERS_PROGRAM_TAB_VIEW

FAKE_COURSE_KEY = CourseKey.from_string('course-v1:fake+course+run')


def strip_course_id(path):
    """
    The utility function to help remove the fake
    course ID from the url path
    """
    course_id = str(FAKE_COURSE_KEY)
    return path.split(course_id)[0]


def program_tab_view_is_enabled() -> bool:
    """
    check if program discussion is enabled.
    """
    return ENABLE_PROGRAM_TAB_VIEW.is_enabled()


def masters_program_tab_view_is_enabled() -> bool:
    """
    check if masters program discussion is enabled.
    """
    return ENABLE_MASTERS_PROGRAM_TAB_VIEW.is_enabled()
