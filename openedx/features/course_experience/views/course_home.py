"""
Views for the course home page.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie

from courseware.courses import get_course_with_access, get_last_accessed_courseware
from lms.djangoapps.courseware.views.views import CourseTabView
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from util.views import ensure_valid_course_key
from web_fragments.fragment import Fragment

from course_outline import CourseOutlineFragmentView


class CourseHomeView(CourseTabView):
    """
    The home page for a course.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id, **kwargs):
        """
        Displays the home page for the specified course.
        """
        return super(CourseHomeView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        course_id = unicode(course.id)
        home_fragment_view = CourseHomeFragmentView()
        return home_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseHomeFragmentView(EdxFragmentView):
    """
    A fragment to render the home page for a course.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course's home page as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        # Render the outline as a fragment
        outline_fragment = CourseOutlineFragmentView().render_to_fragment(request, course_id=course_id, **kwargs)

        # Get the last accessed courseware
        last_accessed_url, __ = get_last_accessed_courseware(course, request, request.user)

        # Render the course home fragment
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'outline_fragment': outline_fragment,
            'has_visited_course': last_accessed_url is not None,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        html = render_to_string('course_experience/course-home-fragment.html', context)
        return Fragment(html)
