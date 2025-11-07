# lint-amnesty, pylint: disable=missing-module-docstring
import logging
from datetime import datetime
from django.conf import settings
from typing import Dict

from opaque_keys.edx.keys import CourseKey
from openedx.core import types

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.course_home_api.toggles import audit_learner_verified_preview_is_enabled

from xmodule.partitions.enrollment_track_partition_generator import (  # lint-amnesty, pylint: disable=wrong-import-order
    create_enrollment_track_partition_with_course_id
)
from xmodule.partitions.partitions import (  # lint-amnesty, pylint: disable=wrong-import-order
    ENROLLMENT_TRACK_PARTITION_ID,
)
from xmodule.partitions.partitions_service import get_user_partition_groups  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.partitions.partitions import Group  # lint-amnesty, pylint: disable=wrong-import-order

from .base import OutlineProcessor

log = logging.getLogger(__name__)


class EnrollmentTrackPartitionGroupsOutlineProcessor(OutlineProcessor):
    """
    Processor for applying all enrollment track user partition groups.

    Confining the processor to only EnrollmentTrack user partition is a
    significant limitation. Nonetheless, it is a step towards the goal of
    supporting all partition schemes in the future.
    """
    def __init__(self, course_key: CourseKey, user: types.User, at_time: datetime):
        super().__init__(course_key, user, at_time)
        self.enrollment_track_groups: Dict[str, Group] = {}
        self.user_group = None

    def load_data(self, full_course_outline) -> None:
        """
        Pull track groups for this course and which group the user is in.
        """
        user_partition = create_enrollment_track_partition_with_course_id(self.course_key)
        self.enrollment_track_groups = get_user_partition_groups(
            self.course_key,
            [user_partition],
            self.user,
            partition_dict_key='id'
        )
        # TODO: fix type annotation: https://github.com/openedx/tcril-engineering/issues/313
        self.user_group = self.enrollment_track_groups.get(ENROLLMENT_TRACK_PARTITION_ID)  # type: ignore

    def _get_user_partition_group_access(self, user_partition_groups):
        """
        Get the user's partition group access for the enrollment track partition.
        """
        is_accessible, is_removed = False, False

        if not user_partition_groups:
            return is_accessible, is_removed

        groups = user_partition_groups.get(ENROLLMENT_TRACK_PARTITION_ID)
        if not groups:
            return is_accessible, is_removed

        if self.user_group and self.user_group.id not in groups:
            # If the user's partition group, say Masters,
            # does not belong to the partition of the block, say [verified],
            # the block should be removed
            is_removed = True

        if audit_learner_verified_preview_is_enabled(self.course_key):
            contains_verified_mode = settings.COURSE_ENROLLMENT_MODES.get(CourseMode.VERIFIED).get('id') in groups
            is_audit_mode = self.user_group and self.user_group.id == settings.COURSE_ENROLLMENT_MODES.get(CourseMode.AUDIT).get('id')

            if is_audit_mode and contains_verified_mode:
                is_accessible = True
                is_removed = False

        return is_accessible, is_removed

    def usage_keys_to_remove(self, full_course_outline):
        """
        Content group exclusions remove the content entirely.

        If you're in the Audit track, there are things in the Verified track
        that you don't even know exists. This processor always removes things
        entirely instead of making them visible-but-inaccessible (like
        ScheduleOutlineProcessor does).
        """
        removed_usage_keys = set()
        for section in full_course_outline.sections:
            remove_all_children = False
            _, should_remove_section = self._get_user_partition_group_access(section.user_partition_groups)
            if should_remove_section:
                removed_usage_keys.add(section.usage_key)
                remove_all_children = True
            for seq in section.sequences:
                _, should_remove_sequence = self._get_user_partition_group_access(seq.user_partition_groups)
                if remove_all_children or should_remove_sequence:
                    removed_usage_keys.add(seq.usage_key)
        return removed_usage_keys

    def inaccessible_sequences(self, full_course_outline):
        """
        TODO
        """
        inaccessible_usage_keys = set()
        for section in full_course_outline.sections:
            remove_all_children = False
            is_section_inaccessible, _ = self._get_user_partition_group_access(section.user_partition_groups)
            if is_section_inaccessible:
                inaccessible_usage_keys.add(section.usage_key)
                remove_all_children = True
            for seq in section.sequences:
                _, is_sequence_inacessible = self._get_user_partition_group_access(seq.user_partition_groups)
                if remove_all_children or is_sequence_inacessible:
                    inaccessible_usage_keys.add(seq.usage_key)
        return inaccessible_usage_keys
