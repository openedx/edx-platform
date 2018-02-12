"""
Portfolio views.
"""

from course_modes.models import get_cosmetic_verified_display_price
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from util.views import ensure_valid_course_key
from web_fragments.fragment import Fragment

from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.views.views import CourseTabView


class GenericTabView(CourseTabView):
    """
    Provides a blank page that acts as its own tab in courseware for displaying content.
    """

    def uses_bootstrap(self, request, course, tab):
        """
        Forces the generic tab to use bootstrap styling.
        """
        return True

    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id, **kwargs):
        """
        Displays a generic tab for the specified course.
        """
        self.course_id = course_id

        return super(GenericTabView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        """
        Render out the bootstrap page.
        """
        course_key = CourseKey.from_string(self.course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)

        upgrade_price = None
        upgrade_url = None

        if enrollment and enrollment.upgrade_deadline:
            upgrade_url = EcommerceService().upgrade_url(request.user, course_key)
            upgrade_price = get_cosmetic_verified_display_price(course)

        context = {
            'course': course,
            'user': request.user,
            'tab_name': tab,
            'upgrade_url': upgrade_url,
            'upgrade_price': upgrade_price,
        }
        html = render_to_string('portfolio_project/generic_tab.html', context)
        return Fragment(html)
