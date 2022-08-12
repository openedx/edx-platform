"""
This module contains  configuration settings via waffle switches for the discussions.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'discussions'

# .. toggle_name: discussions.disable_learners_stats
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to disable learners stats
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-03-02
# .. toggle_target_removal_date: 2022-06-02
# .. toggle_warning: When the flag is ON, API will return learners stats with zero values.
# .. This is temporary fix for performance issue in API.
# .. toggle_tickets: INF-444
DISABLE_LEARNERS_STATS = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.disable_learners_stats', __name__)
