"""
Toggles for course home experience.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = 'course_home'

COURSE_HOME_MICROFRONTEND_PROGRESS_TAB = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_FLAG_NAMESPACE}.course_home_mfe_progress_tab', __name__
)


def course_home_mfe_progress_tab_is_active(course_key):
    # Avoiding a circular dependency
    from .models import DisableProgressPageStackedConfig
    return (
        not course_key.deprecated and
        COURSE_HOME_MICROFRONTEND_PROGRESS_TAB.is_enabled(course_key) and
        not DisableProgressPageStackedConfig.current(course_key=course_key).disabled
    )
