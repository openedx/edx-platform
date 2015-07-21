"""
...
"""
from openedx.core.lib.course_cache.graph_traversals import traverse_topologically
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from courseware.access import _has_access_to_course

# TODO me: Figure out what the value of this should be, and then hard code it in.
ACCESS_TO_ALL_PARENTS_REQUIRED = True


class VisibilityTransformation(CourseStructureTransformation):
    """
    ...
    """
    def collect(self, course_root_block, get_children, get_parents):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformation's apply method.

        Arguments:
            course_root_block (XBlock): Root block of entire course hierarchy.
            get_children (XBlock -> list[XBlock])
            get_parents (XBlock -> list[XBlock])

        Returns:
            dict[UsageKey: dict]
        """
        block_gen = traverse_topologically(
            start_node=course_root_block,
            get_parents=get_parents,
            get_children=get_children,
        )
        compose_parent_access = (
            any if ACCESS_TO_ALL_PARENTS_REQUIRED
            else all
        )
        result_dict = {}
        for block in block_gen:
            # We know that all of the the block's parents have already been
            # visited because we're iterating over the result of a topological
            # sort.
            result_dict[block.usage_key] = {
                'visible_to_staff_only':
                    block.visible_to_staff_only or compose_parent_access(
                        result_dict[parent.usage_key]['visible_to_staff_only']
                        for parent in get_parents(block)
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
            block_structure.remove_if(
                lambda usage_key: (
                    block_data[usage_key].get_transformation_data(
                        self, 'visible_to_staff_only'
                    )
                )
            )


LMS_COURSE_TRANSFORMATIONS = {
    VisibilityTransformation()
}
