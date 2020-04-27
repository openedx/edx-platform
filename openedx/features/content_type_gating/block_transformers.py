"""
Content Type Gate Transformer implementation.
Limits access for certain users to certain types of content.
"""


from django.conf import settings

from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer
from openedx.features.content_type_gating.helpers import CONTENT_GATING_PARTITION_ID
from openedx.features.content_type_gating.models import ContentTypeGatingConfig


class ContentTypeGateTransformer(BlockStructureTransformer):
    """
    A transformer that adds a partition condition for all graded content
    so that the content is only visible to verified users.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "content_type_gate"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields('group_access', 'graded', 'has_score', 'weight')

    def _set_contains_gated_content_on_parents(self, block_structure, block_key):
        """
        This will recursively set a field on all the parents of a block if one of the problems
        inside of it is content gated. `contains_gated_content` can then be used to indicate something
        in the blocks subtree is gated.
        """
        for parent_block_key in block_structure.get_parents(block_key):
            if block_structure.get_xblock_field(parent_block_key, 'contains_gated_content'):
                continue
            block_structure.override_xblock_field(parent_block_key, 'contains_gated_content', True)
            self._set_contains_gated_content_on_parents(block_structure, parent_block_key)

    def transform(self, usage_info, block_structure):
        if not ContentTypeGatingConfig.enabled_for_enrollment(
            user=usage_info.user,
            course_key=usage_info.course_key,
        ):
            return

        for block_key in block_structure.topological_traversal():
            graded = block_structure.get_xblock_field(block_key, 'graded')
            has_score = block_structure.get_xblock_field(block_key, 'has_score')
            weight_not_zero = block_structure.get_xblock_field(block_key, 'weight') != 0
            problem_eligible_for_content_gating = graded and has_score and weight_not_zero
            if problem_eligible_for_content_gating:
                current_access = block_structure.get_xblock_field(block_key, 'group_access')
                if current_access is None:
                    current_access = {}
                current_access.setdefault(
                    CONTENT_GATING_PARTITION_ID,
                    [settings.CONTENT_TYPE_GATE_GROUP_IDS['full_access']]
                )
                block_structure.override_xblock_field(block_key, 'group_access', current_access)
                self._set_contains_gated_content_on_parents(block_structure, block_key)
