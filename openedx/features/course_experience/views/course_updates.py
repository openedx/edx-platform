"""
Views that handle course updates.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control

from courseware.courses import get_course_info_section, get_course_with_access
from lms.djangoapps.courseware.views.views import CourseTabView
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import default_course_url_name
from web_fragments.fragment import Fragment


class CourseUpdatesView(CourseTabView):
    """
    The course updates page.
    """
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request, course_id, **kwargs):
        """
        Displays the home page for the specified course.
        """
        return super(CourseUpdatesView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        course_id = unicode(course.id)
        updates_fragment_view = CourseUpdatesFragmentView()
        return updates_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseUpdatesFragmentView(EdxFragmentView):
    """
    A fragment to render the home page for a course.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course's home page as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(request)
        course_url = reverse(course_url_name, kwargs={'course_id': unicode(course.id)})

        # Fetch the updates as HTML
        updates_html = get_course_info_section(request, request.user, course, 'updates')

        # Render the course home fragment
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_url': course_url,
            'updates_html': updates_html,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        html = render_to_string('course_experience/course-updates-fragment.html', context)
        return Fragment(html)
