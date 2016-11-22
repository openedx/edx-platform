"""
Grading Context
"""
from collections import OrderedDict
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache

from .scores import possibly_scored


def grading_context_for_course(course_key):
    """
    Same as grading_context, but takes in a course object.
    """
    course_structure = get_course_in_cache(course_key)
    return grading_context(course_structure)


def grading_context(course_structure):
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
    all_graded_blocks = []
    all_graded_subsections_by_type = OrderedDict()

    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        for subsection_key in course_structure.get_children(chapter_key):
            subsection = course_structure[subsection_key]
            scored_descendants_of_subsection = []
            if subsection.graded:
                for descendant_key in course_structure.post_order_traversal(
                        filter_func=possibly_scored,
                        start_node=subsection_key,
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
                all_graded_blocks.extend(scored_descendants_of_subsection)

    return {
        'all_graded_subsections_by_type': all_graded_subsections_by_type,
        'all_graded_blocks': all_graded_blocks,
    }
