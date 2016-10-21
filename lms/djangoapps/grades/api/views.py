""" API v0 views. """
import logging

from django.http import Http404
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

log = logging.getLogger(__name__)


class GradeViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def _get_course(self, course_key_string, user, access_action):
        """
        Returns the course for the given course_key_string after
        verifying the requested access to the course by the given user.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
        except InvalidKeyError:
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        try:
            return courses.get_course_with_access(
                user,
                access_action,
                course_key,
                check_if_enrolled=True
            )
        except Http404:
            log.info('Course with ID "%s" not found', course_key_string)
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user, the course or both do not exist.',
                error_code='user_or_course_does_not_exist'
            )

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser), unless DEBUG mode is enabled.
        """
        super(GradeViewMixin, self).perform_authentication(request)
        if request.user.is_anonymous():
            raise AuthenticationFailed


class UserGradeView(GradeViewMixin, GenericAPIView):
    """
    **Use Case**

        * Get the current course grades for users in a course.
          Currently, getting the grade for only an individual user is supported.

    **Example Request**

        GET /api/grades/v0/course_grade/{course_id}/users/?username={username}

    **GET Parameters**

        A GET request must include the following parameters.

        * course_id: A string representation of a Course ID.
        * username: A string representation of a user's username.

    **GET Response Values**

        If the request for information about the course grade
        is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response has the following values.

        * username: A string representation of a user's username passed in the request.

        * course_id: A string representation of a Course ID.

        * passed: Boolean representing whether the course has been
                  passed according the course's grading policy.

        * percent: A float representing the overall grade for the course

        * letter_grade: A letter grade as defined in grading_policy (e.g. 'A' 'B' 'C' for 6.002x) or None


    **Example GET Response**

        [{
            "username": "bob",
            "course_key": "edX/DemoX/Demo_Course",
            "passed": false,
            "percent": 0.03,
            "letter_grade": None,
        }]

    """
    def get(self, request, course_id):
        """
        Gets a course progress status.

        Args:
            request (Request): Django request object.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the requesting user's current grade status.
        """
        username = request.GET.get('username')

        # only the student can access her own grade status info
        if request.user.username != username:
            log.info(
                'User %s tried to access the grade for user %s.',
                request.user.username,
                username
            )
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user requested does not match the logged in user.',
                error_code='user_mismatch'
            )

        course = self._get_course(course_id, request.user, 'load')
        if isinstance(course, Response):
            return course

        prep_course_for_grading(course, request)
        course_grade = CourseGradeFactory(request.user).create(course)
        if not course_grade.has_access_to_course:
            # This means the student didn't have access to the course
            log.info('User %s not allowed to access grade for course %s', request.user.username, username)
            return self.make_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The user does not have access to the course.',
                error_code='user_does_not_have_access_to_course'
            )

        return Response([{
            'username': username,
            'course_key': course_id,
            'passed': course_grade.passed,
            'percent': course_grade.percent,
            'letter_grade': course_grade.letter_grade,
        }])


class CourseGradingPolicy(GradeViewMixin, ListAPIView):
    """
    **Use Case**

        Get the course grading policy.

    **Example requests**:

        GET /api/grades/v0/policy/{course_id}/

    **Response Values**

        * assignment_type: The type of the assignment, as configured by course
          staff. For example, course staff might make the assignment types Homework,
          Quiz, and Exam.

        * count: The number of assignments of the type.

        * dropped: Number of assignments of the type that are dropped.

        * weight: The weight, or effect, of the assignment type on the learner's
          final grade.
    """

    allow_empty = False

    def get(self, request, course_id, **kwargs):
        course = self._get_course(course_id, request.user, 'staff')
        if isinstance(course, Response):
            return course
        return Response(GradingPolicySerializer(course.raw_grader, many=True).data)
