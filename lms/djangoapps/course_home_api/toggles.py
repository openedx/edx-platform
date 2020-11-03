"""
Toggles for course home experience.
"""

from edx_toggles.toggles import WaffleFlagNamespace
from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='course_home')

COURSE_HOME_MICROFRONTEND = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe', __name__)

COURSE_HOME_MICROFRONTEND_DATES_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_dates_tab', __name__)

COURSE_HOME_MICROFRONTEND_OUTLINE_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_outline_tab', __name__)


def course_home_mfe_dates_tab_is_active(course_key):
    return (
        COURSE_HOME_MICROFRONTEND.is_enabled(course_key) and
        COURSE_HOME_MICROFRONTEND_DATES_TAB.is_enabled(course_key)
    )


def course_home_mfe_outline_tab_is_active(course_key):
    return (
        COURSE_HOME_MICROFRONTEND.is_enabled(course_key) and
        COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.is_enabled(course_key)
    )
