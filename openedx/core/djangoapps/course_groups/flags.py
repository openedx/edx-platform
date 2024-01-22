"""Flags for the course_groups app."""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

COURSE_GROUPS_NAMESPACE = "course_groups"

# .. toggle_name: course_groups.content_groups_for_teams
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of content groups for teams.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-11-23
CONTENT_GROUPS_FOR_TEAMS = CourseWaffleFlag(
    f"{COURSE_GROUPS_NAMESPACE}.content_groups_for_teams", __name__
)
