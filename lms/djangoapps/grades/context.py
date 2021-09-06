"""
Grading Context
"""


from collections import OrderedDict

from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache

from .course_grade import CourseGrade
from .scores import possibly_scored


def grading_context_for_course(course):
    """
    Same as grading_context, but takes in a course key.
    """
    course_structure = get_course_in_cache(course.id)
    return grading_context(course, course_structure)


def graded_subsections_for_course(course_structure):
    """
    Given a course block structure, yields the subsections of the course that are graded
    and visible to non-staff users.
    Args:
        course_structure: A course structure object.
    """
    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        for subsection_key in course_structure.get_children(chapter_key):
            subsection = course_structure[subsection_key]
            if not _visible_to_staff_only(subsection) and subsection.graded:
                yield subsection


def grading_context(course, course_structure):
    """
    This returns a dictionary with keys necessary for quickly grading
    a student.

    The grading context has two keys:
    all_graded_subsections_by_type - This contains all subsections that are
        graded, keyed by subsection format (assignment type).

        The values are arrays of dictionaries containing
            "subsection_block" : The subsection block
            "scored_descendants" : An array of usage keys for blocks
                that could possibly be in the subsection, for any student

    all_graded_blocks - This contains a list of all blocks that can
        affect grading a student. This is used to efficiently fetch
        all the xmodule state for a FieldDataCache without walking
        the descriptor tree again.

    """
    count_all_graded_blocks = 0
    all_graded_subsections_by_type = OrderedDict()

    for subsection in graded_subsections_for_course(course_structure):
        scored_descendants_of_subsection = []
        for descendant_key in course_structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=subsection.location,
        ):
            scored_descendants_of_subsection.append(
                course_structure[descendant_key],
            )

        # include only those blocks that have scores, not if they are just a parent
        subsection_info = {
            'subsection_block': subsection,
            'scored_descendants': [
                child for child in scored_descendants_of_subsection
                if getattr(child, 'has_score', None)
            ]
        }
        subsection_format = getattr(subsection, 'format', '')
        if subsection_format not in all_graded_subsections_by_type:
            all_graded_subsections_by_type[subsection_format] = []
        all_graded_subsections_by_type[subsection_format].append(subsection_info)
        count_all_graded_blocks += len(scored_descendants_of_subsection)

    return {
        'all_graded_subsections_by_type': all_graded_subsections_by_type,
        'count_all_graded_blocks': count_all_graded_blocks,
        'subsection_type_graders': CourseGrade.get_subsection_type_graders(course)
    }


def _visible_to_staff_only(subsection):
    """
    Returns True if the given subsection is visible to staff only else False
    """
    try:
        return subsection.transformer_data['visibility'].fields['merged_visible_to_staff_only']
    except KeyError:
        return False
