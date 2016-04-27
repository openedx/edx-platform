"""
Block Depth Transformer
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class BlockDepthTransformer(BlockStructureTransformer):
    """
    Keep track of the depth of each block within the block structure.  In case
    of multiple paths to a given node (in a DAG), use the shallowest depth.
    """
    VERSION = 1
    BLOCK_DEPTH = 'block_depth'

    def __init__(self, requested_depth=None):
        self.requested_depth = requested_depth

    @classmethod
    def name(cls):
        return "blocks_api:block_depth"

    @classmethod
    def get_block_depth(cls, block_structure, block_key):
        """
        Return the precalculated depth of a block within the block_structure:

        Arguments:
            block_structure: a BlockStructure instance
            block_key: the key of the block whose depth we want to know

        Returns:
            int
        """
        return block_structure.get_transformer_block_field(
            block_key,
            cls,
            cls.BLOCK_DEPTH,
        )

    def transform(self, usage_info, block_structure):  # pylint: disable=unused-argument
        """
        Mutates block_structure based on the given usage_info.
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
            block_structure.set_transformer_block_field(
                block_key,
                self,
                self.BLOCK_DEPTH,
                block_depth
            )

        if self.requested_depth is not None:
            block_structure.remove_block_if(
                lambda block_key: self.get_block_depth(block_structure, block_key) > self.requested_depth
            )
