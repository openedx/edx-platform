"""
TODO
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class BlockDepthTransformer(BlockStructureTransformer):
    """
    ...
    """
    VERSION = 1
    BLOCK_DEPTH = 'block_depth'

    def __init__(self, requested_depth=None):
        self.requested_depth = requested_depth

    @classmethod
    def get_block_depth(cls, block_structure, block_key):
        """
        ...
        """
        return block_structure.get_transformer_block_data(
            block_key,
            cls,
            cls.BLOCK_DEPTH,
        )

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        for block_key in block_structure.topological_traversal():
            parents = block_structure.get_parents(block_key)
            if parents:
                block_depth = min(
                    self.get_block_depth(block_structure, parent_key)
                    for parent_key in parents
                ) + 1
            else:
                block_depth = 0
            block_structure.set_transformer_block_data(
                block_key,
                self,
                self.BLOCK_DEPTH,
                block_depth
            )

        if self.requested_depth is not None:
            block_structure.remove_block_if(
                lambda block_key: self.get_block_depth(block_structure, block_key) > self.requested_depth
            )
