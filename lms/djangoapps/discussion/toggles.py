"""
Discussions feature toggles
"""

from openedx.core.djangoapps.discussions.config.waffle import WAFFLE_FLAG_NAMESPACE
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# .. toggle_name: discussions.enable_discussions_mfe
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to use the new MFE experience for discussions in the course tab
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-11-05
# .. toggle_target_removal_date: 2022-12-05
ENABLE_DISCUSSIONS_MFE = CourseWaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.enable_discussions_mfe", __name__
)


# .. toggle_name: discussions.only_verified_users_can_post
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to allow only verified users to post in discussions
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2025-22-07
# .. toggle_target_removal_date: 2026-04-01
ONLY_VERIFIED_USERS_CAN_POST = CourseWaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.only_verified_users_can_post", __name__
)
