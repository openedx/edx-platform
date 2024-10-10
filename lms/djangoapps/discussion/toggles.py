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

FORUM_V2_WAFFLE_FLAG_NAMESPACE = "forum_v2"

# .. toggle_name: forum_v2.enable_forum_v2
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to use the forum v2 instead of v1(cs_comment_service)
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-9-26
# .. toggle_target_removal_date: 2025-12-05
ENABLE_FORUM_V2 = CourseWaffleFlag(
    f"{FORUM_V2_WAFFLE_FLAG_NAMESPACE}.enable_forum_v2", __name__
)


def is_forum_v2_enabled(course_id):
    """
    Returns a boolean if forum V2 is enabled on the course
    """
    return ENABLE_FORUM_V2.is_enabled(course_id)
