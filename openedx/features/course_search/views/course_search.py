"""
Views for the course search page.
"""


import six
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.courses import get_course_overview_with_access
from lms.djangoapps.courseware.views.views import CourseTabView
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import default_course_url_name
from common.djangoapps.util.views import ensure_valid_course_key


class CourseSearchView(CourseTabView):
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
        return super(CourseSearchView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        course_id = six.text_type(course.id)
        home_fragment_view = CourseSearchFragmentView()
        return home_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseSearchFragmentView(EdxFragmentView):
    """
    A fragment to render the home page for a course.
    """

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course's home page as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_overview_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(course.id)})

        # Render the course home fragment
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_key': course_key,
            'course_url': course_url,
            'query': request.GET.get('query', ''),
            'disable_courseware_js': True,
            'uses_bootstrap': True,
        }
        html = render_to_string('course_search/course-search-fragment.html', context)
        return Fragment(html)
