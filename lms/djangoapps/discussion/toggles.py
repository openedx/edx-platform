"""
Discussions feature toggles
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = "discussions"

# .. toggle_name: discussions.enable_discussions_mfe
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to use the new MFE experience for discussions in the course tab and in-context
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-11-05
# .. toggle_target_removal_date: 2022-03-05
ENABLE_DISCUSSIONS_MFE = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_discussions_mfe', __name__)
