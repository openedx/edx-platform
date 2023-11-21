"""
The team dynamic partition generation to be part of the
openedx.dynamic_partition plugin.
"""
import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from openedx.core.djangoapps.course_groups.partition_scheme import CONTENT_GROUPS_FOR_TEAMS

from xmodule.partitions.partitions import UserPartition, UserPartitionError
from xmodule.services import TeamsConfigurationService

log = logging.getLogger(__name__)

FEATURES = getattr(settings, 'FEATURES', {})
MINIMUM_DYNAMIC_TEAM_PARTITION_ID = 51
TEAM_SCHEME = "team"


def create_team_set_partition_with_course_id(course_id, team_sets=None):
    """
    Create and return the dynamic enrollment track user partition based only on course_id.
    If it cannot be created, None is returned.
    """
    if not team_sets:
        team_sets = get_team_sets(course_id) or {}

    try:
        team_scheme = UserPartition.get_scheme(TEAM_SCHEME)
    except UserPartitionError:
        log.warning("No 'team' scheme registered, TeamUserPartition will not be created.")
        return None

    # Get team-sets from course and create user partitions for each team-set
    # Then get teams from each team-set and create user groups for each team
    partitions = []
    for team_set in team_sets:
        partition = team_scheme.create_user_partition(
            id=team_set.dynamic_user_partition_id,
            name=f"Team set {team_set.name} groups",
            description=_("Partition for segmenting users by team-set"),
            parameters={
                "course_id": str(course_id),
                "team_set_id": team_set.teamset_id,
            }
        )
        if partition:
            partitions.append(partition)

    return partitions


def create_team_set_partition(course):
    """
    Get the dynamic enrollment track user partition based on the team-sets of the course.
    """
    if not CONTENT_GROUPS_FOR_TEAMS.is_enabled(course.id):
        return []
    return create_team_set_partition_with_course_id(
        course.id,
        get_team_sets(course.id),
    )


def get_team_sets(course_key):
    """
    Get team-sets of the course.
    """
    team_sets = TeamsConfigurationService().get_teams_configuration(course_key).teamsets
    if not team_sets:
        return None

    return team_sets
