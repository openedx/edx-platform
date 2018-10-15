"""
Start Date Transformer implementation.
"""
from django.conf import settings

from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
)
from openedx.features.content_type_gating.partitions import CONTENT_GATING_PARTITION_ID


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
        block_structure.request_xblock_fields('group_access', 'graded', 'has_score')

    def transform(self, usage_info, block_structure):
        for block_key in block_structure.topological_traversal():
            graded = block_structure.get_xblock_field(block_key, 'graded')
            has_score = block_structure.get_xblock_field(block_key, 'has_score')
            if graded and has_score:
                current_access = block_structure.get_xblock_field(block_key, 'group_access')
                if current_access is None:
                    current_access = {}
                current_access[CONTENT_GATING_PARTITION_ID] = [settings.CONTENT_TYPE_GATE_PARTITION_IDS['unlocked']]
                block_structure.override_xblock_field(block_key, 'group_access', current_access)
