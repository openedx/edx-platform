# lint-amnesty, pylint: disable=missing-module-docstring
import logging

from common.lib.xmodule.xmodule.partitions.enrollment_track_partition_generator import (
    create_enrollment_track_partition_with_course_id
)
from common.lib.xmodule.xmodule.partitions.partitions import (
    ENROLLMENT_TRACK_PARTITION_ID,
)
from common.lib.xmodule.xmodule.partitions.partitions_service import get_user_partition_groups

from .base import OutlineProcessor

log = logging.getLogger(__name__)


class EnrollmentTrackPartitionGroupsOutlineProcessor(OutlineProcessor):
    """
    Processor responsible for applying all enrollment track user partition group to the outline.

    Confining the processor to only EnrollmentTrack user partition is a significant limitation.
    Nonetheless, it is a step towards the goal of supporting
    all partition schemes in the future
    """
    def __init__(self, course_key, user, at_time):
        super().__init__(course_key, user, at_time)
        self.enrollment_track_groups = {}
        self.user_group = None

    def load_data(self):
        user_partition = create_enrollment_track_partition_with_course_id(self.course_key)
        self.enrollment_track_groups = get_user_partition_groups(
            self.course_key,
            [user_partition],
            self.user,
            partition_dict_key='id'
        )
        self.user_group = self.enrollment_track_groups.get(ENROLLMENT_TRACK_PARTITION_ID)

    def _is_user_excluded_by_partition_group(self, user_partition_groups):
        """
        The function to test whether the user is part of the group of which,
        the block is restricting the content to.
        """
        if not user_partition_groups:
            return False

        groups = user_partition_groups.get(ENROLLMENT_TRACK_PARTITION_ID)
        if not groups:
            return False

        if self.user_group and self.user_group.id not in groups:
            # If the user's partition group, say Masters,
            # does not belong to the partition of the block, say [verified],
            # the block should be removed
            return True
        return False

    def usage_keys_to_remove(self, full_course_outline):
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
