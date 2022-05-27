"""
This module contains various configuration settings via
waffle switches for the live app.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'course_live'

# .. toggle_name: course_live.enable_course_live
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the course live app plugin
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-03-02
# .. toggle_target_removal_date: 2022-06-02
# .. toggle_warning: When the flag is ON, the course live app will be visible in the course authoring mfe
# .. toggle_tickets: TNL-9603
ENABLE_COURSE_LIVE = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_course_live', __name__)
