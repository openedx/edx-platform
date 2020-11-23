"""
Visibility Transformer implementation.
"""


from datetime import datetime

from pytz import utc

from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin
)
from xmodule.seq_module import SequenceModule

from .utils import collect_merged_boolean_field, collect_merged_date_field

MAXIMUM_DATE = utc.localize(datetime.max)


class HiddenContentTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A transformer that enforces the hide_after_due field on
    blocks by removing children blocks from the block structure for
    which the user does not have access. The due and hide_after_due
    fields on a block is percolated down to its descendants, so that
    all blocks enforce the hidden content settings from their ancestors.

    For a block with multiple parents, access is denied only if
    access is denied from all its parents.

    Staff users are exempted from hidden content rules.
    """
    WRITE_VERSION = 2
    READ_VERSION = 2
    MERGED_DUE_DATE = 'merged_due_date'
    MERGED_HIDE_AFTER_DUE = 'merged_hide_after_due'

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "hidden_content"

    @classmethod
    def _get_merged_hide_after_due(cls, block_structure, block_key):
        """
        Returns whether the block with the given block_key in the
        given block_structure should be hidden after due date per
        computed value from ancestry chain.
        """
        return block_structure.get_transformer_block_field(
            block_key, cls, cls.MERGED_HIDE_AFTER_DUE, False
        )

    @classmethod
    def _get_merged_due_date(cls, block_structure, block_key):
        """
        Returns the merged value for the start date for the block with
        the given block_key in the given block_structure.
        """
        return block_structure.get_transformer_block_field(
            block_key, cls, cls.MERGED_DUE_DATE, False
        )

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        collect_merged_boolean_field(
            block_structure,
            transformer=cls,
            xblock_field_name='hide_after_due',
            merged_field_name=cls.MERGED_HIDE_AFTER_DUE,
        )

        collect_merged_date_field(
            block_structure,
            transformer=cls,
            xblock_field_name='due',
            merged_field_name=cls.MERGED_DUE_DATE,
            default_date=MAXIMUM_DATE,
            func_merge_parents=max,
            func_merge_ancestors=min,
        )

        block_structure.request_xblock_fields(u'self_paced', u'end')

    def transform_block_filters(self, usage_info, block_structure):
        # Users with staff access bypass the Visibility check.
        if usage_info.has_staff_access:
            return [block_structure.create_universal_filter()]

        return [
            block_structure.create_removal_filter(
                lambda block_key: self._is_block_hidden(block_structure, block_key),
            ),
        ]

    def _is_block_hidden(self, block_structure, block_key):
        """
        Returns whether the block with the given block_key should
        be hidden, given the current time.
        """
        hide_after_due = self._get_merged_hide_after_due(block_structure, block_key)
        self_paced = block_structure[block_structure.root_block_usage_key].self_paced
        if self_paced:
            hidden_date = block_structure[block_structure.root_block_usage_key].end
        else:
            hidden_date = self._get_merged_due_date(block_structure, block_key)
        return not SequenceModule.verify_current_content_visibility(hidden_date, hide_after_due)
