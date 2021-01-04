"""
View logic for handling course welcome messages.
"""


import six
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.courses import get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience.course_updates import (
    dismiss_current_update_for_user, get_current_update_for_user,
)


class WelcomeMessageFragmentView(EdxFragmentView):
    """
    A fragment that displays a course's welcome message.
    """

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the welcome message fragment for the specified course.

        Returns: A fragment, or None if there is no welcome message.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        welcome_message_html = self.welcome_message_html(request, course)
        if not welcome_message_html:
            return None

        dismiss_url = reverse(
            'openedx.course_experience.dismiss_welcome_message', kwargs={'course_id': six.text_type(course_key)}
        )

        context = {
            'dismiss_url': dismiss_url,
            'welcome_message_html': welcome_message_html,
        }

        html = render_to_string('course_experience/welcome-message-fragment.html', context)
        return Fragment(html)

    @classmethod
    def welcome_message_html(cls, request, course):
        """
        Returns the course's welcome message or None if it doesn't have one.
        """
        # Return the course update with the most recent publish date
        return get_current_update_for_user(request, course)


@ensure_csrf_cookie
def dismiss_welcome_message(request, course_id):
    """
    Given the course_id in the request, disable displaying the welcome message for the user.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
    dismiss_current_update_for_user(request, course)
    return HttpResponse()
