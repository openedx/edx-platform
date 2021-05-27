"""
Toggles for course home experience.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='course_home')

# .. toggle_name: course_home.course_home_mfe
# .. toggle_implementation: ExperimentWaffleFlag
# .. toggle_default: False
# .. toggle_description: This experiment flag enables the use of the learning microfrontend (frontend-app-learning)
#   as the default course frontend.
# .. toggle_warnings: For this flag to have an effect, the LEARNING_MICROFRONTEND_URL setting must be configured, too.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2020-05-29
# .. toggle_target_removal_date: 2021-10-09
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-117
COURSE_HOME_MICROFRONTEND = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe', __name__)

COURSE_HOME_MICROFRONTEND_DATES_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_dates_tab', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

COURSE_HOME_MICROFRONTEND_OUTLINE_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_outline_tab', __name__)  # lint-amnesty, pylint: disable=toggle-missing-annotation

COURSE_HOME_MICROFRONTEND_PROGRESS_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'course_home_mfe_progress_tab',  # lint-amnesty, pylint: disable=toggle-missing-annotation
                                                          __name__)


def course_home_mfe_is_active(course_key):
    return (
        COURSE_HOME_MICROFRONTEND.is_enabled(course_key) and
        not course_key.deprecated
    )


def course_home_mfe_dates_tab_is_active(course_key):
    return (
        course_home_mfe_is_active(course_key) and
        COURSE_HOME_MICROFRONTEND_DATES_TAB.is_enabled(course_key)
    )


def course_home_mfe_outline_tab_is_active(course_key):
    return (
        course_home_mfe_is_active(course_key) and
        COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.is_enabled(course_key)
    )


def course_home_mfe_progress_tab_is_active(course_key):
    # Avoiding a circular dependency
    from .models import DisableProgressPageStackedConfig
    return (
        course_home_mfe_is_active(course_key) and
        COURSE_HOME_MICROFRONTEND_PROGRESS_TAB.is_enabled(course_key) and
        not DisableProgressPageStackedConfig.current(course_key=course_key).disabled
    )
