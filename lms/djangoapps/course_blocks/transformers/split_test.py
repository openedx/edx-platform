"""
Split Test Block Transformer
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class SplitTestTransformer(BlockStructureTransformer):
    """
    Split Test Transformer Class
    """
    VERSION = 1

    @classmethod
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureCollectedData)
        """

        root_block = block_structure.get_xblock(block_structure.root_block_key)
        user_partitions = getattr(root_block, 'user_partitions', [])

        for block_key in block_structure.topological_traversal(
            predicate=lambda block_key: block_key.block_type == 'split_test',
            yield_descendants_of_unyielded=True,
        ):
            xblock = block_structure.get_xblock(block_key)
            partition_for_this_block = next(
                (
                    partition for partition in user_partitions
                    if partition.id == xblock.user_partition_id
                ),
                None
            )
            if not partition_for_this_block:
                continue

            # create dict of child location to group_id
            child_to_group = {
                xblock.group_id_to_child.get(unicode(group.id), None): group.id
                for group in partition_for_this_block.groups
            }
            # set group access for each child
            for child_location in xblock.children:
                child = block_structure.get_xblock(child_location)
                group = child_to_group.get(child_location, None)
                child.group_access[partition_for_this_block.id] = [group] if group else []

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info (object)
            block_structure (BlockStructureCollectedData)
        """
        block_structure.remove_block_if(
            lambda block_key: block_key.block_type == 'split_test',
            keep_descendants=True,
        )
