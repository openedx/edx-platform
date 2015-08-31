"""
Split Test Block Transformer, used to filter course structure per user.
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer
from .helpers import get_user_partition_groups


class SplitTestTransformer(BlockStructureTransformer):
    """
    Split Test Transformer Class
    """
    VERSION = 1

    @staticmethod
    def check_split_access(split_test_groups, user_groups):
        """
        Check that user has access to specific split test group.

        Arguments:
            split_test_groups (list)
            user_groups (dict[Partition Id: Group])

        Returns:
            bool
        """
        if split_test_groups:
            for _, group in user_groups.iteritems():
                if group.id in split_test_groups:
                    return True
            return False
        return True

    @classmethod
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureCollectedData)
        """

        # Check potential previously set values for user_partitions and split_test_partitions
        xblock = block_structure.get_xblock(block_structure.root_block_key)
        user_partitions = getattr(xblock, 'user_partitions', [])
        split_test_partitions = getattr(xblock, 'split_test_partition', []) or []

        # For each block, check if there is an split_test block.
        # If split_test is found, check it's user_partition value and get children.
        # Set split_test_group on each of the children for fast retrival in transform phase.
        # Add same group to childrens children, because due to structure restrictions first level
        # children are verticals.
        for block_key in block_structure.topological_traversal():
            xblock = block_structure.get_xblock(block_key)
            category = getattr(xblock, 'category', None)
            if category == 'split_test':
                for user_partition in user_partitions:
                    if user_partition.id == xblock.user_partition_id:
                        if user_partition not in split_test_partitions:
                            split_test_partitions.append(user_partition)
                        for child in xblock.children:
                            for group in user_partition.groups:
                                child_location = xblock.group_id_to_child.get(
                                    unicode(group.id),
                                    None
                                )
                                if child_location == child:
                                    block_structure.set_transformer_block_data(
                                        child,
                                        cls,
                                        'split_test_groups',
                                        [group.id]
                                    )
                                    for component in block_structure.get_xblock(child).children:
                                        block_structure.set_transformer_block_data(
                                            component,
                                            cls,
                                            'split_test_groups',
                                            [group.id]
                                        )

                block_structure.set_transformer_data(cls, 'split_test_partition', split_test_partitions)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info (object)
            block_structure (BlockStructureCollectedData)
        """
        user_partitions = block_structure.get_transformer_data(self, 'split_test_partition')
        # If there are no split test user partitions, this transformation is a no-op,
        # so there is nothing to transform.

        if not user_partitions:
            return

        user_groups = get_user_partition_groups(
            user_info.course_key, user_partitions, user_info.user
        )

        if not user_info.has_staff_access:
            block_structure.remove_block_if(
                lambda block_key: not SplitTestTransformer.check_split_access(
                    block_structure.get_transformer_block_data(
                        block_key, self, 'split_test_groups', default=[]
                    ), user_groups
                )
            )
