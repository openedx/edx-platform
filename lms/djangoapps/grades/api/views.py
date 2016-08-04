""" API v0 views. """
import logging

from django.http import Http404
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

log = logging.getLogger(__name__)


class UserGradeView(DeveloperErrorViewMixin, GenericAPIView):
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
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated, )

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

        # build the course key
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )
        # load the course
        try:
            course = courses.get_course_with_access(
                request.user,
                'load',
                course_key,
                depth=None,
                check_if_enrolled=True
            )
        except Http404:
            log.info('Course with ID "%s" not found', course_id)
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user, the course or both do not exist.',
                error_code='user_or_course_does_not_exist'
            )
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
