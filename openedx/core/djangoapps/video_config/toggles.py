"""
Video config toggles
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = 'video_config'

# .. toggle_name: video_config.public_video_share
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Gates access to the public social sharing video feature.
# .. toggle_use_cases: temporary, opt_in
# .. toggle_creation_date: 2023-02-02
# .. toggle_target_removal_date: None
PUBLIC_VIDEO_SHARE = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.public_video_share', __name__
)
