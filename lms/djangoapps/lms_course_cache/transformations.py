"""
...
"""
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from courseware.access import _has_access_to_course


# TODO me: Figure out what the value of this should be, and then hard code it in.
ACCESS_TO_ALL_PARENTS_REQUIRED = True


class VisibilityTransformation(CourseStructureTransformation):
    """
    ...
    """
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
        compose_parent_access = (
            any if ACCESS_TO_ALL_PARENTS_REQUIRED
            else all
        )
        result_dict = {}
        for block_key in block_structure.topological_traversal():
            # We know that all of the the block's parents have already been
            # visited because we're iterating over the result of a topological
            # sort.
            result_dict[block_key] = {
                'visible_to_staff_only':
                    xblock_dict[block_key].visible_to_staff_only or compose_parent_access(
                        result_dict[parent_key]['visible_to_staff_only']
                        for parent_key in block_structure.get_parents(block_key)
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


LMS_COURSE_TRANSFORMATIONS = {
    VisibilityTransformation(),
}
