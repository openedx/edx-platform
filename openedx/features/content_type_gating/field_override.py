"""
FieldOverride that forces graded components to be only accessible to
students in the Unlocked Group of the ContentTypeGating partition.
"""
from django.conf import settings

from lms.djangoapps.courseware.field_overrides import FieldOverrideProvider, disable_overrides
from openedx.features.content_type_gating.partitions import CONTENT_GATING_PARTITION_ID
from openedx.features.course_duration_limits.config import (
    CONTENT_TYPE_GATING_FLAG,
)


class ContentTypeGatingFieldOverride(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which forces
    graded content to only be accessible to the Full Access group
    """
    def get(self, block, name, default):
        if not CONTENT_TYPE_GATING_FLAG.is_enabled():
            return default

        if name != 'group_access':
            return default

        if not (getattr(block, 'graded', False) and block.has_score):
            return default

        # Read the group_access from the fallback field-data service
        with disable_overrides():
            original_group_access = block.group_access

        if original_group_access is None:
            original_group_access = {}
        original_group_access.setdefault(
            CONTENT_GATING_PARTITION_ID,
            [settings.CONTENT_TYPE_GATE_GROUP_IDS['full_access']]
        )

        return original_group_access

    @classmethod
    def enabled_for(cls, course):
        """This simple override provider is always enabled"""
        return True
