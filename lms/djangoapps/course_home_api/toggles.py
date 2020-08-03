"""
Toggles for course home experience.
"""

from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_home')

COURSE_HOME_MICROFRONTEND = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe')

COURSE_HOME_MICROFRONTEND_DATES_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_dates_tab')


def course_home_mfe_dates_tab_is_active(course_key):
    return (
        COURSE_HOME_MICROFRONTEND.is_enabled(course_key) and
        COURSE_HOME_MICROFRONTEND_DATES_TAB.is_enabled(course_key)
    )
