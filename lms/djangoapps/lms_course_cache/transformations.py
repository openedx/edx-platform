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

def dump(obj):
  for attr in dir(obj):
    print "obj.%s = %s" % (attr, getattr(obj, attr))


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
    def get_group_ids(course, item):
        """

        """
        if hasattr(item, 'group_access') and item.group_access:
            (__, group_ids), = item.group_access.items()
            return group_ids
        return None

    @staticmethod
    def get_group_ids_for_user(course_key, user_partitions, user):
        """ Collect user partition group ids for user for this course """
        partition_groups = []
        for user_partition in user_partitions:
            if user_partition.scheme in INCLUDE_SCHEMES:
                group = UserPartitionTransformation.get_group_for_user_partition(user_partition, course_key, user)
                if group:
                    partition_groups.append(group)
        partition_group_ids = [unicode(partition_group.id) for partition_group in partition_groups]
        return partition_group_ids if partition_group_ids else None

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
            group_ids = UserPartitionTransformation.get_group_ids(course_root_xblock, xblock)
            parent_group_ids = []
            for parent in get_parents(xblock):
                parent_group_ids.append(getattr(result_dict[parent.location], 'group_ids', None))
            result_dict[xblock.location] = {
                'group_ids': 
                    group_ids or compose_parent_access(
                        parent_group_ids
                    ),
                'user_partitions':
                    xblock.user_partitions or compose_parent_access(
                        result_dict[parent.location]['user_partitions']
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
        def remove_condition(root_block_key):
            """
            """
            user_partitions = block_data[root_block_key].get_transformation_data(
                self, 'user_partitions'
            )
            group_ids = block_data[root_block_key].get_transformation_data(
                self, 'group_ids'
            )
            user_groups = UserPartitionTransformation.get_group_ids_for_user(course_key, user_partitions, user)
            if group_ids:
                for group_id in group_ids:
                    if group_id in user_groups:
                        return False
                return True
            return False

        if not _has_access_to_course(user, 'staff', course_key):
            block_structure.remove_block_if(remove_condition)

LMS_COURSE_TRANSFORMATIONS = {
    VisibilityTransformation(), 
    UserPartitionTransformation()
}

