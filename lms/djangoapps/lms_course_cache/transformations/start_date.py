"""
...
"""
from courseware.access import _has_access_to_course
from openedx.core.lib.course_cache.transformation import CourseStructureTransformation


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
        pass  # TODO 8874: Write StartDateTransformation.apply.
