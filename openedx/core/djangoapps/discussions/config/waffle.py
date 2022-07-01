"""
This module contains various configuration settings via
waffle switches for the discussions app.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_NAMESPACE = LegacyWaffleFlagNamespace(name='discussions')

# .. toggle_name: discussions.override_discussion_legacy_settings
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to override visibility of discussion settings for legacy experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-06-15
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warnings: When the flag is ON, the discussion settings will be available on legacy experience.
# .. toggle_tickets: TNL-8389
OVERRIDE_DISCUSSION_LEGACY_SETTINGS_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_NAMESPACE,
    flag_name='override_discussion_legacy_settings',
    module_name=__name__,
)


# .. toggle_name: discussions.pages_and_resources_mfe
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable new Pages and Resources experience for course.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-05-24
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warnings: When the flag is ON, the new experience for Pages and Resources will be enabled.
# .. toggle_tickets: TNL-7791
ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND = CourseWaffleFlag(
    waffle_namespace=WAFFLE_NAMESPACE,
    flag_name='pages_and_resources_mfe',
    module_name=__name__,
)
