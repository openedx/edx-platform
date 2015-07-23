"""
...
"""
from datetime import timedelta

from openedx.core.lib.course_cache.transformation import CourseStructureTransformation
from courseware.access import _has_access_to_course
from xmodule.course_module import DEFAULT_START_DATE


# TODO me: Figure out what the value of this should be, and then hard code it in.
ACCESS_TO_ALL_PARENTS_REQUIRED = False


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
        result_dict = {}
        for block_key in block_structure.topological_traversal():
            # We know that all of the the block's parents have already been
            # visited because we're iterating over the result of a topological
            # sort.
            parent_visibilities = [
                result_dict[parent_key]['merged_student_visibility']
                for parent_key in block_structure.get_parents(block_key)
            ]
            merged_parent_visibility = (
                True if not parent_visibilities
                else all(parent_visibilities) if ACCESS_TO_ALL_PARENTS_REQUIRED
                else any(parent_visibilities)
            )
            result_dict[block_key] = {
                'merged_student_visibility': (
                    not xblock_dict[block_key].visible_to_staff_only
                    and merged_parent_visibility
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
        if _has_access_to_course(user, 'staff', course_key):
            return
        block_structure.remove_block_if(
            lambda block_key: not (
                block_data[block_key].get_transformation_data(self, 'merged_student_visibility')
            ),
            True
        )


class StartDateTransformation(CourseStructureTransformation):
    """
    ...
    """

    @staticmethod
    def merge_start_dates(start, merged_parent_starts):
        """
        Merge together the start date for a block and the start dates of its
        parent blocks.

        None implies that there is no start date restriction.

        Arguments:
            start (datetime or None): Start date of the block, or None if there
                is no start date restriction.
            merged_parent_starts (list[datetime]): Merged start dates of
                this block's parents, or an empty list if none of them have
                start date restrictions.

        Returns:
            datetime or None: The merged start date for the block, or None if
                there is no start date restriction.
        """
        return (
            max(
                start,
                max(merged_parent_starts) if ACCESS_TO_ALL_PARENTS_REQUIRED
                else min(merged_parent_starts)
            )
            if start and merged_parent_starts
            else start or merged_parent_starts
        )

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

        for block_key in block_structure.topological_traversal():
            # We know that all of the the block's parents have already been
            # visited because we're iterating over the result of a topological
            # sort.
            result_dict[block_key] = {}

            xblock = xblock_dict[block_key]
            parent_keys = block_structure.get_parents(block_key)

            start = (
                xblock.start if xblock.start != DEFAULT_START_DATE
                else None
            )
            merged_parent_starts = [
                result_dict[parent_key]['merged_start'] for parent_key in parent_keys
                if 'merged_start' in result_dict[parent_key]
            ]
            merged_start = StartDateTransformation.merge_start_dates(start, merged_parent_starts)

            if merged_start:
                result_dict[block_key]['merged_start'] = merged_start
                beta_start = (
                    start - timedelta(days=xblock.days_early_for_beta) if start and xblock.days_early_for_beta
                    else start
                )
                merged_parent_beta_starts = [
                    result_dict[parent_key]['merged_beta_start'] for parent_key in parent_keys
                    if 'merged_beta_start' in result_dict[parent_key]
                ]
                merged_beta_start = StartDateTransformation.merge_start_dates(beta_start, merged_parent_beta_starts)
                if merged_beta_start and merged_beta_start != merged_start:
                    result_dict[block_key]['merged_beta_start'] = merged_beta_start

        return result_dict

    def apply(self, user, course_key, block_structure, block_data):
        """
        Mutates block_structure and block_data based on the given user_info.

        Arguments:
            user (UserCourseInfo)
            course_key (CourseKey)
            block_structure (CourseBlockStructure)
            block_data (dict[UsageKey: CourseBlockData])
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
    # StartDateTransformation(),  TODO
    # CoursesApiTransformation(), TODO
}
