"""
This module contains various configuration settings via
waffle switches for the discussions app.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_NAMESPACE = 'discussions'

# .. toggle_name: discussions.override_discussion_legacy_settings
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to override visibility of discussion settings for legacy experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-06-15
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warning: When the flag is ON, the discussion settings will be available on legacy experience.
# .. toggle_tickets: TNL-8389
OVERRIDE_DISCUSSION_LEGACY_SETTINGS_FLAG = CourseWaffleFlag(
    f'{WAFFLE_NAMESPACE}.override_discussion_legacy_settings', __name__
)


# .. toggle_name: discussions.pages_and_resources_mfe
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable new Pages and Resources experience for course.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-05-24
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warning: When the flag is ON, the new experience for Pages and Resources will be enabled.
# .. toggle_tickets: TNL-7791
ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND = CourseWaffleFlag(
    f'{WAFFLE_NAMESPACE}.pages_and_resources_mfe', __name__
)
