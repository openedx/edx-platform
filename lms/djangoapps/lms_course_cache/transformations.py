"""
...
"""
from django.utils.translation import ugettext as _

from openedx.core.lib.course_cache.graph_traversals import traverse_topologically
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from courseware.access import _has_access_to_course


INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme, ]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme, ]
# TODO me: Figure out what the value of this should be, and then hard code it in.
ACCESS_TO_ALL_PARENTS_REQUIRED = True


class VisibilityTransformation(CourseStructureTransformation):
    """
    ...
    """
    def collect(self, course_root_xblock, get_children, get_parents):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformation's apply method.

        Arguments:
            course_root_xblock (XBlock): Root block of entire course hierarchy.
            get_children (XBlock -> list[XBlock])
            get_parents (XBlock -> list[XBlock])

        Returns:
            dict[UsageKey: dict]
        """
        xblock_gen = traverse_topologically(
            start_node=course_root_xblock,
            get_parents=get_parents,
            get_children=get_children,
        )
        compose_parent_access = (
            any if ACCESS_TO_ALL_PARENTS_REQUIRED
            else all
        )
        result_dict = {}
        for xblock in xblock_gen:
            # We know that all of the the block's parents have already been
            # visited because we're iterating over the result of a topological
            # sort.
            result_dict[xblock.location] = {
                'visible_to_staff_only':
                    xblock.visible_to_staff_only or compose_parent_access(
                        result_dict[parent.location]['visible_to_staff_only']
                        for parent in get_parents(xblock)
                    )
            }
        return result_dict

    def apply(self, user, course_key, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
        """
        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(
                lambda usage_key: (
                    block_data[usage_key].get_transformation_data(
                        self, 'visible_to_staff_only'
                    )
                )
            )

class UserPartitionTransformation(CourseStructureTransformation):
    """
    ...
    """

    block_data = None

    @staticmethod
    def get_group_ids_for_user(course_key, user_partitions, user):
        """
        Collect group ID for each partition in this course for this user.

        Arguments:
            course_key (CourseKey)
            user_partitions (list[UserPartition])
            user (User)

        Returns:
            dict[int: int]: Mapping from partition IDs to the ID of the group
                to which this user belongs within the partition.
        """
        partition_groups = {}
        for partition_id, user_partition in user_partitions.iteritems():
            if user_partition.scheme in INCLUDE_SCHEMES:
                group = UserPartitionTransformation.get_group_for_user_partition(user_partition, course_key, user)
                if group:
                    partition_groups[user_partition.id] = group
        return partition_groups

    @staticmethod
    def get_group_for_user_partition(user_partition, course_key, user):
        """ Returns the specified user's group for user partition """
        if user_partition.scheme in SCHEME_SUPPORTS_ASSIGNMENT:
            return user_partition.scheme.get_group_for_user(
                course_key,
                user,
                user_partition,
                assign=False,
            )
        else:
            return user_partition.scheme.get_group_for_user(
                course_key,
                user,
                user_partition,
            )

    @staticmethod
    def merge_group_ids(block_group_ids, parent_group_ids):
        """
        Merge together a block's own group IDs and its parents' group IDs
        for a particular partition.

        Arguments:
            block_group_ids (set[int] or None): Set of group IDs for this block,
                or None if this block has no group access restrictions.
            parent_group_ids (list[set[int] or None]): For each of this block's
                parents, a set group IDs or None if the parent has no group
                access restrictions.

        Note:
            merge_group_ids must have already been called on the individual
            sets in parent_group_ids.

        Returns:
            set[int] or None: Set of merged group IDs for this block or None if
                there are no group access restrictions.
        """
        merged_parent_group_ids = None
        if parent_group_ids:
            filtered_parent_group_ids = (
                group_ids for group_ids in parent_group_ids
                if group_ids is not None
            )
            if filtered_parent_group_ids:
                first = next(filtered_parent_group_ids)
                rest = filtered_parent_group_ids
                merged_parent_group_ids = (
                    set(first).intersection(rest)
                    if ACCESS_TO_ALL_PARENTS_REQUIRED
                    else set(first).union(rest)
                )

        # If parents impose no group access restrictions, just use the block's
        # own group IDs.
        if merged_parent_group_ids is None:
            return block_group_ids

        # If the block has no access restrictions, just inherit its parents'.
        elif block_group_ids is None:
            return merged_parent_group_ids

        # Else, take the intersection of the parents' and the block's group IDs.
        else:
            return set(block_group_ids) & merged_parent_group_ids

    def collect(self, course_root_xblock, get_children, get_parents):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformation's apply method.

        Arguments:
            course_root_xblock (XBlock): Root block of entire course hierarchy.
            get_children (XBlock -> list[XBlock])
            get_parents (XBlock -> list[XBlock])

        Returns:
            dict[UsageKey: dict]
        """
        result_dict = {}

        # Because user partitions are coursewide, only store data for them on
        # the root block.
        print 'course_root_xblock'
        print course_root_xblock
        partition_dict = {
            partition.id: partition
            for partition
            in getattr(course_root_xblock, 'user_partitions', []) or []
        }
        if course_root_xblock.location not in result_dict:
            result_dict[course_root_xblock.location] = {}
        result_dict[course_root_xblock.location]['user_partition_dict'] = partition_dict
        if not partition_dict:
            return result_dict  # Course has no partitions, so there is no data to collect.

        # Create a topological traversal of this course, because we need to
        # determine merged_group_ids for parents BEFORE children.
        xblock_gen = traverse_topologically(
            start_node=course_root_xblock,
            get_parents=get_parents,
            get_children=get_children,
        )

        for xblock in xblock_gen:
            for partition_id in partition_dict:

                block_group_ids = []
                if hasattr(xblock, 'group_access'):
                    if partition_id in xblock.group_access:
                        block_group_ids = set(xblock.group_access[partition_id])
                    else:
                        block_group_ids = None

                parents_group_ids = (
                    None
                    if xblock is course_root_xblock
                    else (
                        result_dict[parent.location]['merged_group_access'][partition_id]
                        for parent in get_parents(xblock)
                    )
                )
                merged_group_ids = UserPartitionTransformation.merge_group_ids(
                    block_group_ids, parents_group_ids
                )
                if xblock.location not in result_dict:
                    result_dict[xblock.location] = {}

                if merged_group_ids: 
                    result_dict[xblock.location]['merged_group_access'] = { partition_id: merged_group_ids }
                else: 
                    result_dict[xblock.location]['merged_group_access'] = None

        return result_dict

    def apply(self, user, course_key, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
        """
        user_partitions = block_data[block_structure.root_block_key].get_transformation_data(
            self, 'user_partition_dict'
        )
        # if not user_partitions:
        #     return  # Course has no partitions, so there is nothing to apply.
        user_groups = UserPartitionTransformation.get_group_ids_for_user(course_key, user_partitions, user)
        print 'user_groups'
        print user_groups
        if not user_partitions:
            return  # Course has no partitions, so there is nothing to apply.

        def remove_condition(root_block_key):
            """
            """
            merged_group_access = block_data[root_block_key].get_transformation_data(self, 'merged_group_access')
            for _, partition in user_partitions.iteritems():
                merged_group_ids = []
                if merged_group_access:
                    if partition.id in merged_group_access:
                        merged_group_ids = merged_group_access[partition.id]
                if merged_group_access is None:
                    continue  # No access restrictions; move on to next partition.
                elif merged_group_access == set():
                    return True  # No groups can access this block; remove it.
                elif user_groups[partition.id] not in merged_group_ids:
                    return True  # User is not in one of this block's allowed groups; remove it.
                else:
                    continue  # User is in one of the allowed groups; move on to next partition.
            else:
                return False  # User is in allowed groups for all partitions; don't remove block.
        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(remove_condition)


LMS_COURSE_TRANSFORMATIONS = {
    VisibilityTransformation(), 
    UserPartitionTransformation()
}

