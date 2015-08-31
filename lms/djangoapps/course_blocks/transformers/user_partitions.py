"""
User Partitions Transformer, used to filter course structure per user.
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme

from .helpers import get_user_partition_groups

# TODO 8874: Make it so we support all schemes instead of manually declaring them here.
INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme, ]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme, ]


class MergedGroupAccess(object):
    """
    ...
    """

    # TODO 8874: Make it so LmsBlockMixin.merged_group_access use MergedGroupAccess

    def __init__(self, user_partitions, xblock, merged_parent_access_list):
        """
        Arguments:
            user_partitions (list[UserPartition])
            xblock (XBlock)
            merged_parent_access_list (list[MergedGroupAccess])
        """

        # How group access restrictions are represented within an XBlock:
        #   - group_access not defined                           => No group access restrictions.
        #   - For each partition:
        #       - partition.id not in group_access               => All groups have access for this partition
        #       - group_access[partition_id] is None             => All groups have access for this partition
        #       - group_access[partition_id] == []               => All groups have access for this partition
        #       - group_access[partition_id] == [group1..groupN] => groups 1..N have access for this partition
        #
        # We internally represent the restrictions in a simplified way:
        #   - self._access == {}                                 => No group access restrictions.
        #   - For each partition:
        #       - partition.id not in _access                    => All groups have access for this partition
        #       - _access[partition_id] == set()                 => No groups have access for this partition
        #       - _access[partition_id] == set(group1..groupN)   => groups 1..N have access for this partition
        #
        # Note that a user must have access to all partitions in group_access
        # or _access in order to access a block.

        block_group_access = getattr(xblock, 'group_access', {})
        self._access = {}  # { partition.id: set(IDs of groups that can access partition }

        for partition in user_partitions:

            # Within this loop, None <=> Universe set <=> "No access restriction"

            block_group_ids = set(block_group_access.get(partition.id, [])) or None
            parents_group_ids = [
                merged_parent_access._access[partition.id]
                for merged_parent_access in merged_parent_access_list
                if partition.id in merged_parent_access._access
            ]
            merged_parent_group_ids = (
                set().union(*parents_group_ids)
                if parents_group_ids != []
                else None
            )
            merged_group_ids = MergedGroupAccess._intersection(block_group_ids, merged_parent_group_ids)
            if merged_group_ids is not None:
                self._access[partition.id] = merged_group_ids

    @staticmethod
    def _intersection(*sets):
        """
        Compute an intersection of sets, interpreting None as the Universe set.

        This makes __init__ a bit more elegant.

        Arguments:
            sets (list[set or None]), where None represents the Universe set.

        Returns:
            set or None, where None represents the Universe set.
        """
        non_universe_sets = [set_ for set_ in sets if set_ is not None]
        if non_universe_sets:
            first, rest = non_universe_sets[0], non_universe_sets[1:]
            return first.intersection(*rest)
        else:
            return None

    def check_group_access(self, user_groups):
        """
        Arguments:
            dict[int: Group]: Given a user, a mapping from user partition IDs
                to the group to which the user belongs in each partition.

        Returns:
            bool: Whether said user has group access.
        """
        for partition_id, allowed_group_ids in self._access.iteritems():

            # If the user is not assigned to a group for this partition, deny access.
            # TODO 8874: Ensure that denying access to users who aren't in a group is the correct action.
            if partition_id not in user_groups:
                return False

            # If the user belongs to one of the allowed groups for this partition,
            # then move and check the next partition.
            elif user_groups[partition_id].id in allowed_group_ids:
                continue

            # Else, deny access.
            else:
                return False

        # If the user has access for every partition, grant access.
        else:
            return True


class UserPartitionTransformer(BlockStructureTransformer):
    """
    ...
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
        # Because user partitions are course-wide, only store data for them on the root block.
        root_block = block_structure.get_xblock(block_structure.root_block_key)
        user_partitions = getattr(root_block, 'user_partitions', []) or []
        block_structure.set_transformer_data(cls, 'user_partitions', user_partitions)

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to collect.
        if not user_partitions:
            return

        # For each block, compute merged group access. Because this is a
        # topological sort, we know a block's parents are guaranteed to
        # already have merged group access computed before the block itself.
        for block_key in block_structure.topological_traversal():
            xblock = block_structure.get_xblock(block_key)
            parent_keys = block_structure.get_parents(block_key)
            parent_access = [
                block_structure.get_transformer_block_data(parent_key, cls, 'merged_group_access')
                for parent_key in parent_keys
            ]
            merged_group_access = MergedGroupAccess(user_partitions, xblock, parent_access)
            block_structure.set_transformer_block_data(block_key, cls, 'merged_group_access', merged_group_access)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user_info (object)
            block_structure (BlockStructureCollectedData)
        """
        # TODO 8874: Factor out functionality of UserPartitionTransformation.transform and
        # access._has_group_access into a common utility function.
        user_partitions = block_structure.get_transformer_data(self, 'user_partitions')

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to apply.
        if not user_partitions:
            return

        user_groups = get_user_partition_groups(
            user_info.course_key, user_partitions, user_info.user
        )
        if not user_info.has_staff_access:
            block_structure.remove_block_if(
                lambda block_key: not block_structure.get_transformer_block_data(
                    block_key, self, 'merged_group_access'
                ).check_group_access(user_groups)
            )
