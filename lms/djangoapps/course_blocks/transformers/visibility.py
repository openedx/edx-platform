"""
Visibility Transformer implementation.
"""
from openedx.core.lib.block_structure.transformer import BlockStructureTransformer


class VisibilityTransformer(BlockStructureTransformer):
    """
    A transformer that enforces the visible_to_staff_only field on
    blocks by removing blocks from the block structure for which the
    user does not have access. The visible_to_staff_only field on a
    block is percolated down to its descendants, so that all blocks
    enforce the visibility settings from their ancestors.

    For a block with multiple parents, access is denied only if
    visibility is denied for all its parents.

    Staff users are exempted from visibility rules.
    """
    VERSION = 1

    MERGED_VISIBLE_TO_STAFF_ONLY = 'merged_visible_to_staff_only'

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "visibility"

    @classmethod
    def get_visible_to_staff_only(cls, block_structure, block_key):
        """
        Returns whether the block with the given block_key in the
        given block_structure should be visible to staff only per
        computed value from ancestry chain.
        """
        return block_structure.get_transformer_block_field(
            block_key, cls, cls.MERGED_VISIBLE_TO_STAFF_ONLY, False
        )

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        for block_key in block_structure.topological_traversal():

            # compute merged value of visible_to_staff_only from all parents
            parents = block_structure.get_parents(block_key)
            all_parents_visible_to_staff_only = all(  # pylint: disable=invalid-name
                cls.get_visible_to_staff_only(block_structure, parent_key)
                for parent_key in parents
            ) if parents else False

            # set the merged value for this block
            block_structure.set_transformer_block_field(
                block_key,
                cls,
                cls.MERGED_VISIBLE_TO_STAFF_ONLY,
                # merge visible_to_staff_only from all parents and this block
                (
                    all_parents_visible_to_staff_only or
                    block_structure.get_xblock(block_key).visible_to_staff_only
                )
            )

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        # Users with staff access bypass the Visibility check.
        if usage_info.has_staff_access:
            return

        block_structure.remove_block_if(
            lambda block_key: self.get_visible_to_staff_only(block_structure, block_key)
        )
