"""
Fragment for rendering the course's sock and associated toggle button.
"""
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from student.models import CourseEnrollment
from course_modes.models import CourseMode
from courseware.date_summary import VerifiedUpgradeDeadlineDate
from courseware.views.views import get_cosmetic_verified_display_price
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


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

    def get_verification_context(self, request, course):
        course_key = CourseKey.from_string(unicode(course.id))

        # Establish whether the course has a verified mode
        available_modes = CourseMode.modes_for_course_dict(unicode(course.id))
        has_verified_mode = CourseMode.has_verified_mode(available_modes)

        # Establish whether the user is already enrolled
        is_already_verified = CourseEnrollment.is_enrolled_as_verified(request.user, course_key)

        # Establish whether the verification deadline has already passed
        verification_deadline = VerifiedUpgradeDeadlineDate(course, request.user)
        deadline_has_passed = verification_deadline.deadline_has_passed()

        show_course_sock = has_verified_mode and not is_already_verified and not deadline_has_passed

        # Get the price of the course and format correctly
        course_price = get_cosmetic_verified_display_price(course)

        context = {
            'show_course_sock': show_course_sock,
            'course_price': course_price,
            'course_id': course.id
        }

        return context
