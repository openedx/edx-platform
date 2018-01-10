"""
Views to show a course outline.
"""
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from courseware.courses import get_course_overview_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from ..utils import get_course_outline_block_tree
from util.milestones_helpers import get_course_content_milestones
from xmodule.modulestore.django import modulestore


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

        content_milestones = self.get_content_milestones(request, course_key)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course_overview,
            'blocks': course_block_tree,
            'milestones': content_milestones
        }
        html = render_to_string('course_experience/course-outline-fragment.html', context)
        return Fragment(html)

    def get_content_milestones(self, request, course_key):
        """
        Returns dict of subsections with prerequisites and whether the prerequisite has been completed or not
        """

        all_course_prereqs = get_course_content_milestones(course_key)

        content_ids_of_unfulfilled_prereqs = [
            milestone['content_id']
            for milestone in get_course_content_milestones(course_key, user_id=request.user.id)
        ]

        course_content_milestones = {
            milestone['content_id']: {
                'completed_prereqs': milestone['content_id'] not in content_ids_of_unfulfilled_prereqs
            }
            for milestone in all_course_prereqs
        }

        return course_content_milestones
