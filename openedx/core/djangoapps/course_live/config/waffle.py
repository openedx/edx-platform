"""
This module contains various configuration settings via
waffle switches for the live app.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'course_live'


# .. toggle_name: course_live.enable_big_blue_button
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable big blue button provider
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-06-23
# .. toggle_target_removal_date: 2022-09-23
# .. toggle_warning: When the flag is ON, the big blue button provider will be available in course live
# .. toggle_tickets: INF-308
ENABLE_BIG_BLUE_BUTTON = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_big_blue_button', __name__)
