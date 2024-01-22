"""
Provides a UserPartition driver for teams.
"""
import logging

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.teams.api import get_teams_in_teamset
from lms.djangoapps.teams.models import CourseTeamMembership
from openedx.core.djangoapps.course_groups.flags import CONTENT_GROUPS_FOR_TEAMS
from xmodule.partitions.partitions import (  # lint-amnesty, pylint: disable=wrong-import-order
    Group,
    UserPartition
)
from xmodule.services import TeamsConfigurationService


log = logging.getLogger(__name__)



class TeamUserPartition(UserPartition):
    """
    Extends UserPartition to support dynamic groups pulled from the current course teams.
    """

    team_sets_mapping = {}

    @property
    def groups(self):
        """
        Return the groups (based on CourseModes) for the course associated with this
        EnrollmentTrackUserPartition instance. Note that only groups based on selectable
        CourseModes are returned (which means that Credit will never be returned).
        """
        course_key = CourseKey.from_string(self.parameters["course_id"])
        if not CONTENT_GROUPS_FOR_TEAMS.is_enabled(course_key):
            return []

        team_sets = TeamsConfigurationService().get_teams_configuration(course_key).teamsets
        team_set_id = self.team_sets_mapping[self.id]
        team_set = next((team_set for team_set in team_sets if team_set.teamset_id == team_set_id), None)
        teams = get_teams_in_teamset(str(course_key), team_set.teamset_id)
        return [
            Group(team.id, str(team.name)) for team in teams
        ]


class TeamPartitionScheme:

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition):
        """
        Returns the (Content) Group from the specified user partition to which the user
        is assigned, via their team membership and any mappings from teams to
        partitions / groups that might exist.
        """
        if not CONTENT_GROUPS_FOR_TEAMS.is_enabled(course_key):
            return None

        teams = get_teams_in_teamset(str(course_key), user_partition.parameters["team_set_id"])
        team_ids = [team.team_id for team in teams]
        user_team = CourseTeamMembership.get_memberships(user.username, [str(course_key)], team_ids).first()
        if not user_team:
            return None

        return Group(user_team.team.id, str(user_team.team.name))

    @classmethod
    def create_user_partition(self, id, name, description, groups=None, parameters=None, active=True):
        """
        Create a custom UserPartition to support dynamic groups.

        A Partition has an id, name, scheme, description, parameters, and a list
        of groups. The id is intended to be unique within the context where these
        are used. (e.g., for partitions of users within a course, the ids should
        be unique per-course). The scheme is used to assign users into groups.
        The parameters field is used to save extra parameters e.g., location of
        the course ID for this partition scheme.

        Partitions can be marked as inactive by setting the "active" flag to False.
        Any group access rule referencing inactive partitions will be ignored
        when performing access checks.
        """
        course_key = CourseKey.from_string(parameters["course_id"])
        if not CONTENT_GROUPS_FOR_TEAMS.is_enabled(course_key):
            return None

        # Team-set used to create partition was created before this feature was
        # introduced.  In that case, we need to create a new partition with a
        # new team-set id.
        if not id:
            return

        team_set_partition = TeamUserPartition(
            id,
            str(name),
            str(description),
            groups,
            self,
            parameters,
            active=True,
        )
        TeamUserPartition.team_sets_mapping[id] = parameters["team_set_id"]
        return team_set_partition
