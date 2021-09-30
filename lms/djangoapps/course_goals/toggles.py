"""
Toggles for course goals
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='course_goals')

# .. toggle_name: course_goals.number_of_days_goals
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new version of course goals where users
# .. set a goal for the number of days they want to learn
# .. toggle_warnings: None
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-07-27
# .. toggle_target_removal_date: 2021-09-01
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-859
COURSE_GOALS_NUMBER_OF_DAYS_GOALS = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'number_of_days_goals', __name__)
