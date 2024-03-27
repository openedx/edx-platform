"""Flags for the course_groups app."""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

COURSE_GROUPS_NAMESPACE = "course_groups"

# .. toggle_name: course_groups.content_groups_for_teams
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables content groups for teams. Content groups are virtual groupings of learners
#    who will see a particular set of course content. When this flag is enabled, course authors can create teams and
#    assign content to each of them. Then, when a learner joins a team, they will see the content that is assigned to
#    that team's content group. This flag is only relevant for courses that have teams enabled.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-11-23
CONTENT_GROUPS_FOR_TEAMS = CourseWaffleFlag(
    f"{COURSE_GROUPS_NAMESPACE}.content_groups_for_teams", __name__
)
