"""
Grading Context
"""
from collections import defaultdict
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache

from .scores import possibly_scored


def grading_context_for_course(course):
    """
    Same as grading_context, but takes in a course object.
    """
    course_structure = get_course_in_cache(course.id)
    return grading_context(course_structure)


def grading_context(course_structure):
    """
    This returns a dictionary with keys necessary for quickly grading
    a student. They are used by grades.grade()

    The grading context has two keys:
    graded_sections - This contains the sections that are graded, as
        well as all possible children modules that can affect the
        grading. This allows some sections to be skipped if the student
        hasn't seen any part of it.

        The format is a dictionary keyed by section-type. The values are
        arrays of dictionaries containing
            "section_block" : The section block
            "scored_descendant_keys" : An array of usage keys for blocks
                could possibly be in the section, for any student

    all_graded_blocks - This contains a list of all blocks that can
        affect grading a student. This is used to efficiently fetch
        all the xmodule state for a FieldDataCache without walking
        the descriptor tree again.

    """
    all_graded_blocks = []
    all_graded_sections = defaultdict(list)

    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        for section_key in course_structure.get_children(chapter_key):
            section = course_structure[section_key]
            scored_descendants_of_section = [section]
            if section.graded:
                for descendant_key in course_structure.post_order_traversal(
                        filter_func=possibly_scored,
                        start_node=section_key,
                ):
                    scored_descendants_of_section.append(
                        course_structure[descendant_key],
                    )

                # include only those blocks that have scores, not if they are just a parent
                section_info = {
                    'section_block': section,
                    'scored_descendants': [
                        child for child in scored_descendants_of_section
                        if getattr(child, 'has_score', None)
                    ]
                }
                section_format = getattr(section, 'format', '')
                all_graded_sections[section_format].append(section_info)
                all_graded_blocks.extend(scored_descendants_of_section)

    return {
        'all_graded_sections': all_graded_sections,
        'all_graded_blocks': all_graded_blocks,
    }
