"""
Fragment for rendering the course reviews panel
"""


import six
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.views.views import CourseTabView
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import default_course_url_name
from common.djangoapps.student.models import CourseEnrollment


class CourseReviewsView(CourseTabView):
    """
    The course reviews page.
    """
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request, course_id, **kwargs):
        """
        Displays the reviews page for the specified course.
        """
        return super(CourseReviewsView, self).get(request, course_id, 'courseware', **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        course_id = six.text_type(course.id)
        reviews_fragment_view = CourseReviewsFragmentView()
        return reviews_fragment_view.render_to_fragment(request, course_id=course_id, **kwargs)


class CourseReviewsFragmentView(EdxFragmentView):
    """
    A fragment to display course reviews.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Fragment to render the course reviews fragment.

        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(course.id)})

        is_enrolled = CourseEnrollment.is_enrolled(request.user, course.id)

        # Create the fragment
        course_reviews_fragment = CourseReviewsModuleFragmentView().render_to_fragment(
            request,
            course=course,
            **kwargs
        )

        context = {
            'course': course,
            'course_url': course_url,
            'course_reviews_fragment': course_reviews_fragment,
            'is_enrolled': is_enrolled,
        }

        html = render_to_string('course_experience/course-reviews-fragment.html', context)
        return Fragment(html)


class CourseReviewsModuleFragmentView(EdxFragmentView):
    """
    A fragment to display the course reviews module as specified by
    the configured template.
    """

    def render_to_fragment(self, request, course=None, **kwargs):
        """
        Renders the configured template as a module.

        There are two relevant configuration settings:

        COURSE_REVIEWS_TOOL_PROVIDER_FRAGMENT_NAME points to the template that
        will be rendered and returned.

        COURSE_REVIEWS_TOOL_PROVIDER_PLATFORM_KEY references the platform that
        hosts the course. Generally, this is the domain name of the platform,
        for example, 'edx.org' would have a platform key of 'edx'.

        """
        # Grab the fragment type and provider from the configuration file
        course_reviews_fragment_provider_template = \
            settings.COURSE_REVIEWS_TOOL_PROVIDER_FRAGMENT_NAME
        course_platform_key = \
            settings.COURSE_REVIEWS_TOOL_PROVIDER_PLATFORM_KEY

        if not self.is_configured():
            return None

        context = {
            'course': course,
            'platform_key': course_platform_key
        }

        # Create the fragment from the given template
        provider_reviews_template = 'course_experience/course_reviews_modules/%s' \
                                    % course_reviews_fragment_provider_template

        html = render_to_string(provider_reviews_template, context)
        return Fragment(html)

    @classmethod
    def is_configured(self):
        return settings.COURSE_REVIEWS_TOOL_PROVIDER_FRAGMENT_NAME \
            and settings.COURSE_REVIEWS_TOOL_PROVIDER_PLATFORM_KEY
