"""
...
"""
class CourseStructureTransformation(object):
    """
    ...
    """

    @property
    def id(self):
        """
        Returns:
            str
        """
        return self.__class__.__name__

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

    def apply(self, user, course_key, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (UserCourseInfo)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
        """
        pass
