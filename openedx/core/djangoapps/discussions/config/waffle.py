"""
This module contains various configuration settings via
waffle switches for the discussions app.
"""
from django.conf import settings

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = "discussions"

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
    f"{WAFFLE_FLAG_NAMESPACE}.override_discussion_legacy_settings", __name__
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
    f"{WAFFLE_FLAG_NAMESPACE}.pages_and_resources_mfe", __name__
)

# .. toggle_name: discussions.enable_new_structure_discussions
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to toggle on the new structure for in context discussions
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-02-22
# .. toggle_target_removal_date: 2022-12-22
ENABLE_NEW_STRUCTURE_DISCUSSIONS = CourseWaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.enable_new_structure_discussions", __name__
)

# .. toggle_name: discussions.enable_forum_v2
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to use the forum v2 instead of v1(cs_comment_service)
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-9-26
# .. toggle_target_removal_date: 2025-12-05
ENABLE_FORUM_V2 = CourseWaffleFlag(f"{WAFFLE_FLAG_NAMESPACE}.enable_forum_v2", __name__)


def is_forum_v2_enabled(course_key):
    """
    Returns whether forum V2 is enabled on the course. This is a 2-step check:

    1. Check value of settings.DISABLE_FORUM_V2: if it exists and is true, this setting overrides any course flag.
    2. Else, check the value of the corresponding course waffle flag.
    """
    if is_forum_v2_disabled_globally():
        return False
    return ENABLE_FORUM_V2.is_enabled(course_key)


def is_forum_v2_disabled_globally() -> bool:
    """
    Return True if DISABLE_FORUM_V2 is defined and true-ish.
    """
    return getattr(settings, "DISABLE_FORUM_V2", False)
