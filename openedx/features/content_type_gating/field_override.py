"""
FieldOverride that forces graded components to be only accessible to
students in the Unlocked Group of the ContentTypeGating partition.
"""


from django.conf import settings

from lms.djangoapps.courseware.field_overrides import FieldOverrideProvider
from openedx.features.content_type_gating.helpers import CONTENT_GATING_PARTITION_ID
from openedx.features.content_type_gating.models import ContentTypeGatingConfig


class ContentTypeGatingFieldOverride(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which forces
    graded content to only be accessible to the Full Access group
    """
    def get(self, block, name, default):
        if name != 'group_access':
            return default

        graded = getattr(block, 'graded', False)
        has_score = block.has_score
        weight_not_zero = getattr(block, 'weight', 0) != 0
        problem_eligible_for_content_gating = graded and has_score and weight_not_zero
        if not problem_eligible_for_content_gating:
            return default

        # We want to fetch the value set by course authors since it should take precedence.
        # We cannot simply call "block.group_access" to fetch that value even if we disable
        # field overrides since it will set the group access field to "dirty" with
        # the value read from the course content. Since most content does not have any
        # value for this field it will usually be the default empty dict. This field
        # override changes the value, however, resulting in the LMS thinking that the
        # field data needs to be written back out to the store. This doesn't work,
        # however, since this is a read-only setting in the LMS context. After this
        # call to get() returns, the _dirty_fields dict will be set correctly to contain
        # the value from this field override. This prevents the system from attempting
        # to save the overridden value when it thinks it has changed when it hasn't.
        original_group_access = None
        if self.fallback_field_data.has(block, 'group_access'):
            raw_value = self.fallback_field_data.get(block, 'group_access')
            group_access_field = block.fields.get('group_access')
            if group_access_field is not None:
                original_group_access = group_access_field.from_json(raw_value)

        if original_group_access is None:
            original_group_access = {}

            # For Feature Based Enrollments, we want to inherit group access configurations
            # from parent blocks. The use case is to allow granting access
            # to all graded problems in a unit at the unit level
            parent = block.get_parent()
            if parent is not None:
                merged_group_access = parent.merged_group_access
                if merged_group_access and CONTENT_GATING_PARTITION_ID in merged_group_access:
                    return default

        original_group_access.setdefault(
            CONTENT_GATING_PARTITION_ID,
            [settings.CONTENT_TYPE_GATE_GROUP_IDS['full_access']]
        )

        return original_group_access

    @classmethod
    def enabled_for(cls, course):
        """Check our stackable config for this specific course"""
        return ContentTypeGatingConfig.enabled_for_course(course_key=course.scope_ids.usage_id.course_key)
