"""
Provides a UserPartition driver for cohorts.
"""


import logging

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.masquerade import (
    get_course_masquerade,
    get_masquerading_user_group,
    is_masquerading_as_specific_student
)
from lms.djangoapps.teams.api import get_teams_in_teamset
from lms.djangoapps.teams.models import CourseTeamMembership
from xmodule.partitions.partitions import (  # lint-amnesty, pylint: disable=wrong-import-order
    Group,
    NoSuchUserPartitionGroupError,
    UserPartition
)
from xmodule.services import TeamsConfigurationService
from openedx.core.djangoapps.course_groups.flags import CONTENT_GROUPS_FOR_TEAMS

from .cohorts import get_cohort, get_group_info_for_cohort

log = logging.getLogger(__name__)


class CohortPartitionScheme:
    """
    This scheme uses lms cohorts (CourseUserGroups) and cohort-partition
    mappings (CourseUserGroupPartitionGroup) to map lms users into Partition
    Groups.
    """

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition, use_cached=True):
        """
        Returns the Group from the specified user partition to which the user
        is assigned, via their cohort membership and any mappings from cohorts
        to partitions / groups that might exist.

        If the user has not yet been assigned to a cohort, an assignment *might*
        be created on-the-fly, as determined by the course's cohort config.
        Any such side-effects will be triggered inside the call to
        cohorts.get_cohort().

        If the user has no cohort mapping, or there is no (valid) cohort ->
        partition group mapping found, the function returns None.
        """
        # First, check if we have to deal with masquerading.
        # If the current user is masquerading as a specific student, use the
        # same logic as normal to return that student's group. If the current
        # user is masquerading as a generic student in a specific group, then
        # return that group.
        if get_course_masquerade(user, course_key) and not is_masquerading_as_specific_student(user, course_key):
            return get_masquerading_user_group(course_key, user, user_partition)

        cohort = get_cohort(user, course_key, use_cached=use_cached)
        if cohort is None:
            # student doesn't have a cohort
            return None

        group_id, partition_id = get_group_info_for_cohort(cohort, use_cached=use_cached)
        if partition_id is None:
            # cohort isn't mapped to any partition group.
            return None

        if partition_id != user_partition.id:
            # if we have a match but the partition doesn't match the requested
            # one it means the mapping is invalid.  the previous state of the
            # partition configuration may have been modified.
            log.warning(
                "partition mismatch in CohortPartitionScheme: %r",
                {
                    "requested_partition_id": user_partition.id,
                    "found_partition_id": partition_id,
                    "found_group_id": group_id,
                    "cohort_id": cohort.id,
                }
            )
            # fail silently
            return None

        try:
            return user_partition.get_group(group_id)
        except NoSuchUserPartitionGroupError:
            # if we have a match but the group doesn't exist in the partition,
            # it means the mapping is invalid.  the previous state of the
            # partition configuration may have been modified.
            log.warning(
                "group not found in CohortPartitionScheme: %r",
                {
                    "requested_partition_id": user_partition.id,
                    "requested_group_id": group_id,
                    "cohort_id": cohort.id,
                },
                exc_info=True
            )
            # fail silently
            return None


def get_cohorted_user_partition(course):
    """
    Returns the first user partition from the specified course which uses the CohortPartitionScheme,
    or None if one is not found. Note that it is currently recommended that each course have only
    one cohorted user partition.
    """
    for user_partition in course.user_partitions:
        if user_partition.scheme == CohortPartitionScheme:
            return user_partition

    return None


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
