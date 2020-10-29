"""
View logic for handling course messages.
"""

from django.template.loader import render_to_string
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


class NextUpBannerFragmentView(EdxFragmentView):
    """
    A fragment that displays an up next banner with a call to action to resume the course.
    """

    # pylint: disable=arguments-differ
    def render_to_fragment(self, assignment_title, resume_course_url, assignment_duration='10 mins'):
        """
        Renders an up next banner fragment with the provided assignment title, duration, and a link to the URL.
        """
        context = {
            'assignment_title': assignment_title,
            'resume_course_url': resume_course_url,
            'assignment_duration': assignment_duration,
        }
        html = render_to_string('course_experience/next-up-banner-fragment.html', context)
        return Fragment(html)
