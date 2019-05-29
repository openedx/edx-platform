"""
Fragment for rendering the course's sock and associated toggle button.
"""
from __future__ import absolute_import

from django.template.loader import render_to_string
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.course_modes.models import get_cosmetic_verified_display_price
from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from student.models import CourseEnrollment


class CourseSockFragmentView(EdxFragmentView):
    """
    A fragment to provide extra functionality in a dropdown sock.
    """
    def render_to_fragment(self, request, course, **kwargs):
        """
        Render the course's sock fragment.
        """
        context = self.get_verification_context(request, course)
        html = render_to_string('course_experience/course-sock-fragment.html', context)
        return Fragment(html)

    @staticmethod
    def get_verification_context(request, course):
        enrollment = CourseEnrollment.get_enrollment(request.user, course.id)
        show_course_sock = verified_upgrade_link_is_valid(enrollment)
        if show_course_sock:
            upgrade_url = verified_upgrade_deadline_link(request.user, course=course)
            course_price = get_cosmetic_verified_display_price(course)
        else:
            upgrade_url = ''
            course_price = ''

        context = {
            'show_course_sock': show_course_sock,
            'course_price': course_price,
            'course_id': course.id,
            'upgrade_url': upgrade_url,
        }

        return context
