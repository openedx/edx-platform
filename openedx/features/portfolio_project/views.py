"""
Portfolio views.
"""

from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control

from lms.djangoapps.courseware.views.views import CourseTabView

from util.views import ensure_valid_course_key

from web_fragments.fragment import Fragment


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
        return super(GenericTabView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        """
        Render out the bootstrap page.
        """
        context = {
            'course': course,
            'user': request.user,
            'tab_name': tab,
        }
        html = render_to_string('portfolio_project/generic_tab.html', context)
        return Fragment(html)
