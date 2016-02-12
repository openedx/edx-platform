"""
Block Counts Transformer
"""
from openedx.core.lib.block_structure.transformer import BlockStructureTransformer


class BlockCountsTransformer(BlockStructureTransformer):
    """
    Keep a count of descendant blocks of the requested types
    """
    VERSION = 1
    BLOCK_COUNTS = 'block_counts'

    def __init__(self, block_types_to_count):
        self.block_types_to_count = block_types_to_count

    @classmethod
    def name(cls):
        return "blocks_api:block_counts"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields('category')

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        if not self.block_types_to_count:
            return

        for block_key in block_structure.post_order_traversal():
            for block_type in self.block_types_to_count:
                descendants_type_count = sum([
                    block_structure.get_transformer_block_field(child_key, self, block_type, 0)
                    for child_key in block_structure.get_children(block_key)
                ])
                block_structure.set_transformer_block_field(
                    block_key,
                    self,
                    block_type,
                    (
                        descendants_type_count +
                        (1 if (block_structure.get_xblock_field(block_key, 'category') == block_type) else 0)
                    )
                )
