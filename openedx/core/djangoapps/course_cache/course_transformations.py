"""
...
"""
from openedx.core.lib.graph_traversals import traverse_topologically


class CourseStructureTransformation(object):
    """
    ...
    """

    def __init__(self, transformation_id):
        """
        Arguments:
            transformation_id (str):  A unique string to identify this transformation.
        """
        self.id = transformation_id

    @property
    def required_fields(self):
        """
        Specifies XBlock fields that are required by this transformation's
        apply method.

        Returns:
            set[xblocks.fields.Field]
        """
        return set()

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
        return {}

    def apply(self, root_block_key, user_info, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            root_block_key (UsageKey)
            user_info (UserCourseInfo)
            block_structure (CourseBlockStructure)
            block_data (CourseBlockData)
        """
        pass


class VisibilityTransformation(CourseStructureTransformation):
    """
    ...
    """

    def __init__(self, transformation_id, parent_access_rule):
        """
        Arguments:
            transformation_id (str): A unique string to identify this transformation.
            parent_access_rule (MultiParentAccessRule)
        """
        super(VisibilityTransformation, self).__init__(transformation_id)
        self.parent_access_rule = parent_access_rule

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
            any if self.parent_access_rule == MultiParentAccessRule.ACCESS_TO_ALL_REQUIRED
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

    def apply(self, user_info, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            root_block_key (UsageKey)
            user_info (UserCourseInfo)
            block_structure (CourseBlockStructure)
            block_data (CourseBlockData)
        """
        if user_info.has_staff_access:
            return
        block_structure.remove_if(
            lambda usage_key: (
                block_data[usage_key].get_transformation_data(
                    self, 'visible_to_staff_only'
                )
            )
        )


class MultiParentAccessRule(object):
    """
    ...
    """
    ACCESS_TO_ALL_REQUIRED = 0
    ACCESS_TO_ANY_REQUIRED = 1
