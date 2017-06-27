"""
Fragment for rendering the course dates sidebar.
"""
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from courseware.courses import get_course_date_blocks, get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


class CourseDatesFragmentView(EdxFragmentView):
    """
    A fragment to important dates within a course.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Render the course dates fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)
        course_date_blocks = get_course_date_blocks(course, request.user)

        context = {
            'course_date_blocks': course_date_blocks
        }
        html = render_to_string('course_experience/course-dates-fragment.html', context)
        return Fragment(html)
