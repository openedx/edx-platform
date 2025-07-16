"""
Feature toggles for the offline mode app.
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = 'offline_mode'

# .. toggle_name: offline_mode.enable_offline_mode
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This feature toggle enables the offline mode course
#       content generation for mobile devices.
# .. toggle_use_cases: opt_out, open_edx
# .. toggle_creation_date: 2024-06-06
# .. toggle_target_removal_date: None
ENABLE_OFFLINE_MODE = CourseWaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.enable_offline_mode', __name__)


def is_offline_mode_enabled(course_key=None):
    """
    Returns True if the offline mode is enabled for the course, False otherwise.
    """
    return ENABLE_OFFLINE_MODE.is_enabled(course_key)
