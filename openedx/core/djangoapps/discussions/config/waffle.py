"""
This module contains various configuration settings via
waffle switches for the discussions app.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_DISCUSSION_LEGACY_SETTINGS_NAMESPACE = LegacyWaffleFlagNamespace(name='discussions')

# .. toggle_name: discussions.override_discussion_legacy_settings
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to override visibility of discussion settings for legacy experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-06-15
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warnings: Discussion settings will be visible when this flag is enabled with Pages & Resources flag enabled.
# .. toggle_tickets: https://openedx.atlassian.net/browse/TNL-8389
OVERRIDE_DISCUSSION_LEGACY_SETTINGS_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_DISCUSSION_LEGACY_SETTINGS_NAMESPACE,
    flag_name='override_discussion_legacy_settings',
    module_name=__name__,
)
