"""
Toggles for course home experience.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = 'course_home'

# .. toggle_name: course_home.course_home_mfe_progress_tab
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This toggle controls the user interface behavior of the progress tab in
#   the Learning Management System. When set to True, the progress tab utilizes the newly introduced
#   Learning MFE graphs. When set to False (default), it utilizes existing grade graph from edx-platform.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-03-12
# .. toggle_target_removal_date: 2024-01-01
# .. toggle_tickets: https://github.com/openedx/edx-platform/pull/26978
COURSE_HOME_MICROFRONTEND_PROGRESS_TAB = CourseWaffleFlag(
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
