"""
Progress Tab Views
"""

from django.http.response import Http404
from edx_django_utils import monitoring as monitoring_utils
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from xmodule.modulestore.django import modulestore
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_home_api.progress.v1.serializers import ProgressTabSerializer
from lms.djangoapps.course_home_api.toggles import course_home_mfe_progress_tab_is_active
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary, get_course_with_access, get_studio_url
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.courseware.views.views import get_cert_data

from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class ProgressTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Progress Tab

    **Example Requests**

        GET api/course_home/v1/progress/{course_key}

    **Response Values**

        Body consists of the following fields:

        certificate_data: Object containing information about the user's certificate status
            cert_status: (str) the status of a user's certificate (full list of statuses are defined in
                         lms/djangoapps/certificates/models.py)
            cert_web_view_url: (str) the url to view the certificate
            download_url: (str) the url to download the certificate
        completion_summary: Object containing unit completion counts with the following fields:
            complete_count: (float) number of complete units
            incomplete_count: (float) number of incomplete units
            locked_count: (float) number of units where contains_gated_content is True
        course_grade: Object containing the following fields:
            is_passing: (bool) whether the user's grade is above the passing grade cutoff
            letter_grade: (str) the user's letter grade based on the set grade range.
                                If user is passing, value may be 'A', 'B', 'C', 'D', 'Pass', otherwise none
            percent: (float) the user's total graded percent in the course
        section_scores: List of serialized Chapters. Each Chapter has the following fields:
            display_name: (str) a str of what the name of the Chapter is for displaying on the site
            subsections: List of serialized Subsections, each has the following fields:
                assignment_type: (str) the format, if any, of the Subsection (Homework, Exam, etc)
                display_name: (str) a str of what the name of the Subsection is for displaying on the site
                has_graded_assignment: (bool) whether or not the Subsection is a graded assignment
                num_points_earned: (int) the amount of points the user has earned for the given subsection
                num_points_possible: (int) the total amount of points possible for the given subsection
                percent_graded: (float) the percentage of total points the user has received a grade for in a given subsection
                show_correctness: (str) a str representing whether to show the problem/practice scores based on due date
                                  ('always', 'never', 'past_due', values defined in
                                   common/lib/xmodule/xmodule/modulestore/inheritance.py)
                show_grades: (bool) a bool for whether to show grades based on the access the user has
                url: (str) the absolute path url to the Subsection
        enrollment_mode: (str) a str representing the enrollment the user has ('audit', 'verified', ...)
        grading_policy:
            assignment_policies: List of serialized assignment grading policy objects, each has the following fields:
                num_droppable: (int) the number of lowest scored assignments that will not be counted towards the final grade
                short_label: (str) the abbreviated name given to the assignment type
                type: (str) the assignment type
                weight: (float) the percent weight the given assigment type has on the overall grade
            grade_range: an object containing the grade range cutoffs. The exact keys in the object can vary, but they
                         range from just 'Pass', to a combination of 'A', 'B', 'C', and 'D'. If a letter grade is present,
                         'Pass' is not included.
        studio_url: (str) a str of the link to the grading in studio for the course
        verification_data: an object containing
            link: (str) the link to either start or retry verification
            status: (str) the status of the verification
            status_date: (str) the date time string of when the verification status was set

    **Returns**

        * 200 on success with above fields.
        * 302 if the user is not enrolled.
        * 401 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)
    serializer_class = ProgressTabSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)

        if not course_home_mfe_progress_tab_is_active(course_key):
            raise Http404

        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_attribute('course_id', course_key_string)
        monitoring_utils.set_custom_attribute('user_id', request.user.id)
        monitoring_utils.set_custom_attribute('is_staff', request.user.is_staff)

        _, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True
        )

        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        enrollment_mode, _ = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)

        course_grade = CourseGradeFactory().read(request.user, course)\

        descriptor = modulestore().get_course(course_key)
        grading_policy = descriptor.grading_policy

        verification_status = IDVerificationService.user_status(request.user)
        verification_link = None
        if verification_status['status'] is None or verification_status['status'] == 'expired':
            verification_link = IDVerificationService.get_verify_location(course_id=course_key)
        elif verification_status['status'] == 'must_reverify':
            verification_link = IDVerificationService.get_verify_location(course_id=course_key)
        verification_data = {
            'link': verification_link,
            'status': verification_status['status'],
            'status_date': verification_status['status_date'],
        }

        data = {
            'certificate_data': get_cert_data(request.user, course, enrollment_mode, course_grade),
            'completion_summary': get_course_blocks_completion_summary(course_key, request.user),
            'course_grade': course_grade,
            'section_scores': course_grade.chapter_grades.values(),
            'enrollment_mode': enrollment_mode,
            'grading_policy': grading_policy,
            'studio_url': get_studio_url(course, 'settings/grading'),
            'verification_data': verification_data,
        }
        context = self.get_serializer_context()
        context['staff_access'] = bool(has_access(request.user, 'staff', course))
        context['course_key'] = course_key
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)
