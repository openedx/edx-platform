"""
...
"""
from datetime import timedelta

from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from courseware.access import _has_access_to_course
from xmodule.course_module import DEFAULT_START_DATE


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
    # CoursesApiTransformation(), TODO
}
