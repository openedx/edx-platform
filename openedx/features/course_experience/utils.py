"""
Common utilities for the course experience, including course outline.
"""
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.utils import get_student_module_as_dict
from openedx.core.lib.cache_utils import memoized
from xmodule.modulestore.django import modulestore


@memoized
def get_course_outline_block_tree(request, course_id):
    """
    Returns the root block of the course outline, with children as blocks.
    """

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def set_last_accessed_default(block):
        """
        Set default of False for last_accessed on all blocks.
        """
        block['last_accessed'] = False
        for child in block.get('children', []):
            set_last_accessed_default(child)

    def mark_last_accessed(user, course_key, block):
        """
        Recursively marks the branch to the last accessed block.
        """
        block_key = block.serializer.instance
        student_module_dict = get_student_module_as_dict(user, course_key, block_key)
        last_accessed_child_position = student_module_dict.get('position')
        if last_accessed_child_position and block.get('children'):
            block['last_accessed'] = True
            if last_accessed_child_position <= len(block['children']):
                last_accessed_child_block = block['children'][last_accessed_child_position - 1]
                last_accessed_child_block['last_accessed'] = True
                mark_last_accessed(user, course_key, last_accessed_child_block)
            else:
                # We should be using an id in place of position for last accessed. However, while using position, if
                # the child block is no longer accessible we'll use the last child.
                block['children'][-1]['last_accessed'] = True

    course_key = CourseKey.from_string(course_id)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=request.user,
        nav_depth=3,
        requested_fields=['children', 'display_name', 'type', 'due', 'graded', 'special_exam_info', 'format'],
        block_types_filter=['course', 'chapter', 'sequential']
    )

    course_outline_root_block = all_blocks['blocks'][all_blocks['root']]
    populate_children(course_outline_root_block, all_blocks['blocks'])
    set_last_accessed_default(course_outline_root_block)
    mark_last_accessed(request.user, course_key, course_outline_root_block)

    return course_outline_root_block
