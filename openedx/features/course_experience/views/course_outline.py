"""
Views to show a course outline.
"""

from django.core.context_processors import csrf
from django.template.loader import render_to_string

from courseware.courses import get_course_with_access, get_last_accessed_courseware
from lms.djangoapps.course_api.blocks.api import get_blocks
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from web_fragments.fragment import Fragment
from xmodule.modulestore.django import modulestore


class CourseOutlineFragmentView(EdxFragmentView):
    """
    Course outline fragment to be shown in the unified course view.
    """

    def populate_children(self, block, all_blocks, course_position):
        """
        For a passed block, replace each id in its children array with the full representation of that child,
        which will be looked up by id in the passed all_blocks dict.
        Recursively do the same replacement for children of those children.
        """
        children = block.get('children') or []

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = self.populate_children(all_blocks[child_id], all_blocks, course_position)

            block['children'][i] = child_detail
            block['children'][i]['current'] = course_position == child_detail['block_id']

        return block

    def render_to_fragment(self, request, course_id=None, page_context=None, **kwargs):
        """
        Renders the course outline as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        _, course_position = get_last_accessed_courseware(course, request, request.user)
        course_usage_key = modulestore().make_course_usage_key(course_key)
        all_blocks = get_blocks(
            request,
            course_usage_key,
            user=request.user,
            nav_depth=3,
            requested_fields=['children', 'display_name', 'type', 'due', 'graded', 'special_exam_info', 'format'],
            block_types_filter=['course', 'chapter', 'sequential']
        )

        course_block_tree = all_blocks['blocks'][all_blocks['root']]  # Get the root of the block tree

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            # Recurse through the block tree, fleshing out each child object
            'blocks': self.populate_children(course_block_tree, all_blocks['blocks'], course_position)
        }
        html = render_to_string('course_experience/course-outline-fragment.html', context)
        return Fragment(html)
