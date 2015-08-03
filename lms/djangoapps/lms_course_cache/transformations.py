"""
...
"""
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from courseware.access import _has_access_to_course


INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme,]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme,]


class VisibilityTransformation(CourseStructureTransformation):
    """
    ...
    """

    @property
    def required_fields(self):
        """
        Specifies XBlock fields that are required by this transformation's
        apply method.

        Returns:
            set[str]
        """
        return {'visible_to_staff_only'}

    def apply(self, user, course_key, block_structure, block_data, remove_orphans):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
            remove_orphans (bool)
        """
        if _has_access_to_course(user, 'staff', course_key):
            return
        block_structure.remove_block_if(
            lambda block_key: block_data[block_key].get_xblock_field('visible_to_staff_only'),
            remove_orphans,
        )


class StartDateTransformation(CourseStructureTransformation):
    """
    ...
    """

    @property
    def required_fields(self):
        """
        Specifies XBlock fields that are required by this transformation's
        apply method.

        Returns:
            set[str]
        """
        return {'start', 'days_early_for_beta'}

    def apply(self, user, course_key, block_structure, block_data, remove_orphans):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (User)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
            remove_orphans (bool)
        """
        pass  # TODO


class UserPartitionTransformation(CourseStructureTransformation):
    """
    ...
    """

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
                merged_parent_group_ids = set().union(filtered_parent_group_ids)

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
        if not partition_dict:
            return result_dict  # Course has no partitions, so there is no data to collect.

        for block_key in block_structure.topological_traversal():
            result_dict[block_key] = {}

            for partition_id in partition_dict:

                xblock = xblock_dict[block_key]
                block_group_ids = (
                    set(xblock.group_access[partition_id])
                    if hasattr(xblock, 'group_access') and partition_dict in xblock.group_access
                    else None
                ) or None

                parents_group_ids = (
                    None
                    if block_key == block_structure.root_block_key
                    else (
                        result_dict[parent.location]['merged_group_access'][partition_id]
                        for parent in block_structure.get_parents(block_key)
                    )
                )
                merged_group_ids = UserPartitionTransformation.merge_group_ids(
                    block_group_ids, parents_group_ids
                )
                result_dict[xblock.location]['merged_group_access'][partition_id] = merged_group_ids

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
        # TODO me: This will break if the block_structure.root_block_key is not the course
        user_partitions = block_data[block_structure.root_block_key].get_transformation_data(
            self, 'user_partition_dict'
        )
        if not user_partitions:
            return  # Course has no partitions, so there is nothing to apply.
        user_groups = UserPartitionTransformation.get_group_ids_for_user(course_key, user_partitions, user)

        def remove_condition(block_key):
            """
            Arguments:
                block_key (UsageKey)
            """
            merged_group_access = block_data[block_key].get_transformation_data(self, 'merged_group_access')

            for partition in user_partitions.values():
                merged_group_ids = merged_group_access[partition.id]

                # If there are no access restrictions for this partition, move on
                # to the next one.
                if merged_group_ids is None:
                    continue

                # If the user is not in an allowed group for this partition,
                # remove the block.
                elif user_groups[partition.id] not in merged_group_ids:
                    return True

            # User is in allowed groups for all partitions; don't remove block.
            return False

        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(remove_condition)


class CoursesApiTransformation(CourseStructureTransformation):
    """
    ...
    """
    @property
    def required_fields(self):
        """
        Specifies XBlock fields that are required by this transformation's
        apply method.

        Returns:
            set[str]
        """
        # TODO: finish
        return {
            'id',
            'type',
            'display_name',
            'lms_web_url',
            'olx_data',
            'student_view_url',
            'student_view_data',
        }

LMS_COURSE_TRANSFORMATIONS = {
    VisibilityTransformation(),
    StartDateTransformation(),
    UserPartitionTransformation(),
    # CoursesApiTransformation(), TODO
}
