"""
Views to show a course outline.
"""
import re

from django.template.context_processors import csrf
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from courseware.courses import get_course_overview_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import waffle as waffle

from ..utils import get_course_outline_block_tree
from util.milestones_helpers import get_course_content_milestones


class CourseOutlineFragmentView(EdxFragmentView):
    """
    Course outline fragment to be shown in the unified course view.
    """

    def render_to_fragment(self, request, course_id=None, page_context=None, **kwargs):
        """
        Renders the course outline as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course_overview = get_course_overview_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        course_block_tree = get_course_outline_block_tree(request, course_id)
        if not course_block_tree:
            return None

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course_overview,
            'blocks': course_block_tree
        }

        # TODO: EDUCATOR-2283 Remove this check when the waffle flag is turned on in production
        if waffle.new_course_outline_enabled(course_key=course_key):
            xblock_display_names = self.create_xblock_id_and_name_dict(course_block_tree)

            gated_content = self.get_content_milestones(request, course_key)

            context['gated_content'] = gated_content
            context['xblock_display_names'] = xblock_display_names

            # TODO: EDUCATOR-2283 Rename this file to course-outline-fragment.html
            html = render_to_string('course_experience/course-outline-fragment-new.html', context)
            return Fragment(html)
        else:
            content_milestones = self.get_content_milestones_old(request, course_key)

            context['gated_content'] = content_milestones

            # TODO: EDUCATOR-2283 Remove this file
            html = render_to_string('course_experience/course-outline-fragment-old.html', context)
            return Fragment(html)

    def create_xblock_id_and_name_dict(self, course_block_tree, xblock_display_names=None):
        """
        Creates a dictionary mapping xblock IDs to their names, using a course block tree.
        """
        if xblock_display_names is None:
            xblock_display_names = {}

        if course_block_tree.get('id'):
            xblock_display_names[course_block_tree['id']] = course_block_tree['display_name']

        if course_block_tree.get('children'):
            for child in course_block_tree['children']:
                self.create_xblock_id_and_name_dict(child, xblock_display_names)

        return xblock_display_names

    def get_content_milestones(self, request, course_key):
        """
        Returns dict of subsections with prerequisites and whether the prerequisite has been completed or not
        """
        def _get_key_of_prerequisite(namespace):
            return re.sub('.gating', '', namespace)

        all_course_milestones = get_course_content_milestones(course_key)

        uncompleted_prereqs = {
            milestone['content_id']
            for milestone in get_course_content_milestones(course_key, user_id=request.user.id)
        }

        gated_content = {
            milestone['content_id']: {
                'completed_prereqs': milestone['content_id'] not in uncompleted_prereqs,
                'prerequisite': _get_key_of_prerequisite(milestone['namespace'])
            }
            for milestone in all_course_milestones
        }

        return gated_content

    # TODO: EDUCATOR-2283 Remove this function when the visual progress waffle flag is turned on in production
    def get_content_milestones_old(self, request, course_key):
        """
        Returns dict of subsections with prerequisites and whether the prerequisite has been completed or not
        """

        all_course_prereqs = get_course_content_milestones(course_key)

        content_ids_of_unfulfilled_prereqs = {
            milestone['content_id']
            for milestone in get_course_content_milestones(course_key, user_id=request.user.id)
        }

        course_content_milestones = {
            milestone['content_id']: {
                'completed_prereqs': milestone['content_id'] not in content_ids_of_unfulfilled_prereqs
            }
            for milestone in all_course_prereqs
        }

        return course_content_milestones
