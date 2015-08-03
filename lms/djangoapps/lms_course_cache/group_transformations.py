"""
...
"""
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from courseware.access import _has_access_to_course


INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme,]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme,]


class MergedGroupAccess(object):
    """
    ...
    """

    def __init__(self, partition_ids, xblock, merged_parent_access_list):
        """
        Arguments:
            partition_ids (list[int])
            xblock (XBlock)
            merged_parent_access_list (dict[UsageKey: MergedGroupAccess])
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
        #   - self._partition_dict == {}                                 => No group access restrictions.
        #   - For each partition:
        #       - partition.id not in _partition_access                  => All groups have access for this partition
        #       - _partition_access[partition_id] == set()               => No groups have access for this partition
        #       - _partition_access[partition_id] == set(group1..groupN) => groups 1..N have access for this partition
        #
        # Note that a user must have access to all partitions in group_access
        # or _partition_dict in order to access a block.

        block_group_access = getattr(xblock, 'group_access', {})

        for partition_id in partition_ids:

            # Within this loop, None <=> Universe set <=> "No access restriction"

            block_group_ids = set(block_group_access.get(partition_id, [])) or None
            parents_group_ids = [
                merged_parent_access[partition_id]
                for merged_parent_access in merged_parent_access_list.values()
                if partition_id in merged_parent_access_list
            ]
            merged_parent_group_ids = (
                set().union(*parents_group_ids) if parents_group_ids != []
                else None
            )
            merged_group_ids = MergedGroupAccess._intersection(block_group_ids, merged_parent_group_ids)
            if merged_group_ids is not None:
                self._partition_access[partition_id] = merged_group_ids

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
            user_groups (dict[int: int]): Dictionary in the form: {
                    partition1.id: group1.id,
                    partition2.id: group2.id,
                    ...
                    partitionN.id: groupN.id
                }
                where groupX is the group of partitionY to which the user
                belongs.

        Returns:
            bool: Whether said user
        """
        # TODO me: is this the correct behavior for partitions in which user doesn't belong to a group?
        for partition_id, allowed_group_ids in self._partition_dict.iteritems():
            group_id = user_groups.get(partition_id, None)
            if group_id not in allowed_group_ids:
                return False
        else:
            return True


class UserPartitionTransformation(CourseStructureTransformation):
    """
    ...
    """

    @staticmethod
    def _get_group_for_user_partition(course_key, user_partition, user):
        """
        Compute the user's group for the given user partition.

        Arguments:
            course_key(CourseKey)
            user_partition (UserPartition)
            user (User)

        Returns:
            Group or None
        """
        kwargs = (
            {'assign': False} if user_partition.scheme in SCHEME_SUPPORTS_ASSIGNMENT
            else {}
        )
        return user_partition.scheme.get_group_for_user(
            course_key,
            user,
            user_partition,
            **kwargs
        )

    @staticmethod
    def _get_group_ids_for_user(course_key, user_partitions, user):
        """
        Collect group ID for each partition in this course for this user.

        Arguments:
            course_key (CourseKey)
            user_partitions (dict[int: UserPartition])
            user (User)

        Returns:
            dict[int: int]: Dictionary in the form: {
                partition1.id: group1.id,
                partition2.id: group2.id,
                ...
                partitionN.id: groupN.id
            }
            where groupX is the group of partitionY to which the user belongs.

        Note:
            (partitionA.id not in return_value) => user is not assigned a
                group for partitionA.
        """
        partition_groups = {}
        for partition_id, user_partition in user_partitions.iteritems():
            if user_partition.scheme not in INCLUDE_SCHEMES:
                continue
            group = UserPartitionTransformation._get_group_for_user_partition(course_key, user_partition, user)
            if not group:
                continue
            partition_groups[partition_id] = group
        return partition_groups

    def collect(self, course_key, block_structure, xblock_dict):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformation's apply method.

        Arguments:
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            xblock_dict (dict[UsageKey: XBlock])

        Returns:
            dict[UsageKey: dict]
        """
        result_dict = {}

        # Because user partitions are course-wide, only store data for them on
        # the root block.
        partition_dict = {
            partition.id: partition
            for partition
            in getattr(xblock_dict[block_structure.root_block_key], 'user_partitions', []) or []
        }
        result_dict[block_structure.root_block_key]['user_partition_dict'] = partition_dict

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to collect.
        if not partition_dict:
            return result_dict

        # For each block, compute merged group access. Because this is a
        # topological sort, we know a block's parents are guaranteed to
        # already have merged group access computed before the block itself.
        for block_key in block_structure.topological_sort():
            xblock = xblock_dict[block_key]
            parent_keys = block_structure.get_parents(block_key)
            parent_access = [result_dict[parent_key]['merged_group_access'] for parent_key in parent_keys]
            merged_group_access = MergedGroupAccess(partition_dict.keys(), xblock, parent_access)
            result_dict[block_key]['merged_group_access'] = merged_group_access

    def apply(self, user, course_key, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
        """
        # TODO me: This will break if the block_structure.root_block_key is not the course
        user_partition_dict = block_data[block_structure.root_block_key].get_transformation_data(
            self, 'user_partition_dict'
        )

        # If there are no user partitions, this transformation is a no-op,
        # so there is nothing to apply.
        if not user_partition_dict:
            return

        user_groups = UserPartitionTransformation._get_group_ids_for_user(
            course_key, user_partition_dict, user
        )
        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(
                lambda block_key: block_data[block_key].get_transformation_data(
                    self, 'merged_group_access'
                ).check_group_access(user_groups)
            )