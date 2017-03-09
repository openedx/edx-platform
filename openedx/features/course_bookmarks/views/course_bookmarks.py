"""
Views to show a course's bookmarks.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from courseware.courses import get_course_with_access
from lms.djangoapps.courseware.tabs import CoursewareTab
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from util.views import ensure_valid_course_key
from web_fragments.fragment import Fragment
from xmodule.modulestore.django import modulestore


class CourseBookmarksView(View):
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
        course_url_name = CoursewareTab.main_course_url_name(request)
        course_url = reverse(course_url_name, kwargs={'course_id': unicode(course.id)})

        # Render the bookmarks list as a fragment
        outline_fragment = CourseBookmarksFragmentView().render_to_fragment(request, course_id=course_id)

        # Render the entire unified course view
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_url': course_url,
            'outline_fragment': outline_fragment,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        return render_to_response('course_bookmarks/course-bookmarks.html', context)


class CourseBookmarksFragmentView(EdxFragmentView):
    """
    Fragment view that shows a user's bookmarks for a course.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course outline as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'bookmarks_api_url': reverse('bookmarks'),
            'language_preference': 'en',  # TODO:
        }
        html = render_to_string('course_bookmarks/course-bookmarks-fragment.html', context)
        inline_js = render_to_string('course_bookmarks/course_bookmarks_js.template', context)
        fragment = Fragment(html)
        self.add_fragment_resource_urls(fragment)
        fragment.add_javascript(inline_js)
        return fragment
