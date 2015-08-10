"""
...
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class VisibilityTransformer(BlockStructureTransformer):
    """
    ...
    """
    VERSION = 1

    MERGED_VISIBLE_TO_STAFF_ONLY = 'merged_visible_to_staff_only'

    @classmethod
    def get_visible_to_staff_only(cls, block_structure, block_key):
        return block_structure.get_transformer_block_data(
            block_key, cls, cls.MERGED_VISIBLE_TO_STAFF_ONLY, False
        )

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        for block_key in block_structure.topological_traversal():

            # compute merged value of visible_to_staff_only from all parents
            parents = block_structure.get_parents(block_key)
            all_parents_visible_to_staff_only = all(
                cls.get_visible_to_staff_only(block_structure, parent_key)
                for parent_key in parents
            ) if parents else False

            # set the merged value for this block
            block_structure.set_transformer_block_data(
                block_key,
                cls,
                cls.MERGED_VISIBLE_TO_STAFF_ONLY,
                # merge visible_to_staff_only from all parents and this block
                (
                    all_parents_visible_to_staff_only or
                    block_structure.get_xblock(block_key).visible_to_staff_only
                )
            )

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        if user_info.has_staff_access:
            return

        block_structure.remove_block_if(
            lambda block_key: self.get_visible_to_staff_only(block_structure, block_key)
        )
