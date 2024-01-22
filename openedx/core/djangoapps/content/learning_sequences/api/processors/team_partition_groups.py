"""
Outline processors for applying team user partition groups.
"""
import logging
from datetime import datetime
from typing import Dict

from opaque_keys.edx.keys import CourseKey

from openedx.core import types
from openedx.core.djangoapps.content.learning_sequences.api.processors.base import OutlineProcessor
from openedx.core.djangoapps.course_groups.partition_generator import create_team_set_partition_with_course_id
from openedx.core.djangoapps.course_groups.flags import CONTENT_GROUPS_FOR_TEAMS
from xmodule.partitions.partitions import Group
from xmodule.partitions.partitions_service import get_user_partition_groups

log = logging.getLogger(__name__)


class TeamPartitionGroupsOutlineProcessor(OutlineProcessor):
    """
    Processor for applying all team user partition groups.

    This processor is used to remove content from the course outline based on
    the user's team membership. It is used in the courseware API to remove
    content from the course outline before it is returned to the client.
    """
    def __init__(self, course_key: CourseKey, user: types.User, at_time: datetime):
        super().__init__(course_key, user, at_time)
        self.team_groups: Dict[str, Group] = {}
        self.user_group = None

    def load_data(self, _) -> None:
        """
        Pull team groups for this course and which group the user is in.
        """
        user_partitions = create_team_set_partition_with_course_id(self.course_key)
        self.team_groups = get_user_partition_groups(
            self.course_key,
            user_partitions,
            self.user,
            partition_dict_key="id",
        )
        self.user_groups = []
        for _, group in self.team_groups.items():
            self.user_groups.append(group.id)

    def _is_user_excluded_by_partition_group(self, user_partition_groups):
        """
        Is the user part of the group to which the block is restricting content?

        The user is excluded if the block is in a partition group, but the user
        is not in that group.
        """
        if not CONTENT_GROUPS_FOR_TEAMS.is_enabled(self.course_key):
            return False

        if not user_partition_groups:
            return False

        if not self.user_groups:
            return False

        for partition_id, groups in user_partition_groups.items():
            if partition_id not in self.team_groups:
                continue
            if self.team_groups[partition_id].id in groups:
                return False

        return True

    def usage_keys_to_remove(self, full_course_outline):
        """
        Content group exclusions remove the content entirely.

        This method returns the usage keys of all content that should be
        removed from the course outline based on the user's team membership.
        """
        removed_usage_keys = set()
        for section in full_course_outline.sections:
            remove_all_children = False
            if self._is_user_excluded_by_partition_group(
                section.user_partition_groups
            ):
                removed_usage_keys.add(section.usage_key)
                remove_all_children = True
            for seq in section.sequences:
                if remove_all_children or self._is_user_excluded_by_partition_group(
                    seq.user_partition_groups
                ):
                    removed_usage_keys.add(seq.usage_key)
        return removed_usage_keys
