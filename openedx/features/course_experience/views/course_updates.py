"""
Views that handle course updates.
"""

import six
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.courses import get_course_info_section_module, get_course_with_access
from lms.djangoapps.courseware.views.views import CourseTabView
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import default_course_url_name
from openedx.features.course_experience.course_updates import get_ordered_updates


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
        course_id = six.text_type(course.id)
        updates_fragment_view = CourseUpdatesFragmentView()
        return updates_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseUpdatesFragmentView(EdxFragmentView):
    """
    A fragment to render the updates page for a course.
    """

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the course's home page as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(course.id)})

        ordered_updates = get_ordered_updates(request, course)
        plain_html_updates = ''
        if ordered_updates:
            plain_html_updates = self.get_plain_html_updates(request, course)

        # Render the course home fragment
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_url': course_url,
            'updates': ordered_updates,
            'plain_html_updates': plain_html_updates,
            'disable_courseware_js': True,
        }
        html = render_to_string('course_experience/course-updates-fragment.html', context)
        return Fragment(html)

    @classmethod
    def has_updates(self, request, course):
        return len(get_ordered_updates(request, course)) > 0

    @classmethod
    def get_plain_html_updates(self, request, course):
        """
        Returns any course updates in an html chunk. Used
        for older implementations and a few tests that store
        a single html object representing all the updates.
        """
        info_module = get_course_info_section_module(request, request.user, course, 'updates')
        info_block = getattr(info_module, '_xmodule', info_module)
        return info_block.system.replace_urls(info_module.data) if info_module else ''
