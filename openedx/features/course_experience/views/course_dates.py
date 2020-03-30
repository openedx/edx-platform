"""
Fragment for rendering the course dates sidebar.
"""


from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import get_language_bidi
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from openedx.features.course_experience.utils import reset_deadlines_banner_should_display

from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


class CourseDatesFragmentView(EdxFragmentView):
    """
    A fragment to important dates within a course.
    """
    template_name = 'course_experience/course-dates-fragment.html'

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Render the course dates fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)
        course_date_blocks = get_course_date_blocks(course, request.user, request, num_assignments=2)

        context = {
            'course_date_blocks': [block for block in course_date_blocks if block.title != 'current_datetime']
        }
        html = render_to_string(self.template_name, context)
        dates_fragment = Fragment(html)
        self.add_fragment_resource_urls(dates_fragment)

        return dates_fragment


class CourseDatesFragmentMobileView(CourseDatesFragmentView):
    """
    A course dates fragment to show dates on mobile apps.

    Mobile apps uses WebKit mobile client to create and maintain a session with
    the server for authenticated requests, and it hasn't exposed any way to find
    out either session was created with the server or not so mobile app uses a
    mechanism to automatically create/recreate session with the server for all
    authenticated requests if the server returns 404.
    """
    template_name = 'course_experience/mobile/course-dates-fragment.html'

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404
        return super(CourseDatesFragmentMobileView, self).get(request, *args, **kwargs)

    def css_dependencies(self):
        """
        Returns list of CSS files that this view depends on.

        The helper function that it uses to obtain the list of CSS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        if get_language_bidi():
            return self.get_css_dependencies('style-mobile-rtl')
        else:
            return self.get_css_dependencies('style-mobile')

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Render the course dates fragment.
        """
        from lms.urls import RESET_COURSE_DEADLINES_NAME
        from openedx.features.course_experience.urls import COURSE_DATES_FRAGMENT_VIEW_NAME

        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)
        course_date_blocks = get_course_date_blocks(course, request.user, request, num_assignments=2)

        display_reset_dates_banner = False

        if RELATIVE_DATES_FLAG.is_enabled(course.id):
            display_reset_dates_banner = reset_deadlines_banner_should_display(course_key, request)

        reset_deadlines_url = reverse(RESET_COURSE_DEADLINES_NAME) if display_reset_dates_banner else None

        reset_deadlines_redirect_url_base = COURSE_DATES_FRAGMENT_VIEW_NAME if (
            reset_deadlines_url) else None

        context = {
            'course_date_blocks': [block for block in course_date_blocks if block.title != 'current_datetime'],
            'display_reset_dates_banner': display_reset_dates_banner,
            'reset_deadlines_url': reset_deadlines_url,
            'reset_deadlines_redirect_url_base': reset_deadlines_redirect_url_base,
            'reset_deadlines_redirect_url_id_dict': {'course_id': course_id}
        }
        html = render_to_string(self.template_name, context)
        dates_fragment = Fragment(html)
        self.add_fragment_resource_urls(dates_fragment)

        return dates_fragment
