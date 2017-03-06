"""
Views for the course home page.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from courseware.courses import get_course_with_access
from opaque_keys.edx.keys import CourseKey
from util.views import ensure_valid_course_key

from course_outline import CourseOutlineFragmentView


class CourseHomeView(View):
    """
    The home page for a course.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Displays the home page for the specified course.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        # Render the outline as a fragment
        outline_fragment = CourseOutlineFragmentView().render_to_fragment(request, course_id=course_id)

        # Render the entire unified course view
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'outline_fragment': outline_fragment,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        return render_to_response('course_experience/course-home.html', context)
