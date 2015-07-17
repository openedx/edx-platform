"""
...
"""

class CourseStructureTransformation(object):
    """
    ...
    """

    def __init__(self, transformation_id):
        """
        Arguments:
            transformation_id (str): A unique string to identify this transformation.
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
