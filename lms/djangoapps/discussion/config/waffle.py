"""
This module contains  configuration settings via waffle switches for the discussions.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'discussions'

# .. toggle_name: discussions.enable_learners_stats
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable learners stats
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-08-12
# .. toggle_target_removal_date: 2022-10-02
# .. toggle_warning: When the flag is ON, API will return learners stats with original values.
# .. This is temporary fix for performance issue in API.
# .. toggle_tickets: INF-444
ENABLE_LEARNERS_STATS = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_learners_stats', __name__)
