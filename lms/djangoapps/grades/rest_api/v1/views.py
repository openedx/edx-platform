""" API v0 views. """


import logging
from contextlib import contextmanager

from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.grades.api import CourseGradeFactory, clear_prefetched_course_grades, prefetch_course_grades
from lms.djangoapps.grades.rest_api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.rest_api.v1.utils import CourseEnrollmentPagination, GradeViewMixin
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import PaginatedAPIView, get_course_key, verify_course_exists
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger(__name__)


@contextmanager
def bulk_course_grade_context(course_key, users):
    """
    Prefetches grades for the given users in the given course
    within a context, storing in a RequestCache and deleting
    on context exit.
    """
    prefetch_course_grades(course_key, users)
    try:
        yield
    finally:
        clear_prefetched_course_grades(course_key)


class CourseGradesView(GradeViewMixin, PaginatedAPIView):
    """
    **Use Case**
        * Get course grades of all users who are enrolled in a course.
        The currently logged-in user may request all enrolled user's grades information
        if they are allowed.
    **Example Request**
        GET /api/grades/v1/courses/{course_id}/                              - Get grades for all users in course
        GET /api/grades/v1/courses/{course_id}/?username={username}          - Get grades for specific user in course
        GET /api/grades/v1/courses/?course_id={course_id}                    - Get grades for all users in course
        GET /api/grades/v1/courses/?course_id={course_id}&username={username}- Get grades for specific user in course
    **GET Parameters**
        A GET request may include the following parameters.
        * course_id: (required) A string representation of a Course ID.
        * username:  (optional) A string representation of a user's username.
    **GET Response Values**
        If the request for information about the course grade
        is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response has the following values.
        * username: A string representation of a user's username passed in the request.
        * email: A string representation of a user's email.
        * course_id: A string representation of a Course ID.
        * passed: Boolean representing whether the course has been
                  passed according to the course's grading policy.
        * percent: A float representing the overall grade for the course
        * letter_grade: A letter grade as defined in grading policy (e.g. 'A' 'B' 'C' for 6.002x) or None
    **Example GET Response**
        [{
            "username": "bob",
            "email": "bob@example.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "passed": false,
            "percent": 0.03,
            "letter_grade": null,
        },
        {
            "username": "fred",
            "email": "fred@example.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "passed": true,
            "percent": 0.83,
            "letter_grade": "B",
        },
        {
            "username": "kate",
            "email": "kate@example.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "passed": false,
            "percent": 0.19,
            "letter_grade": null,
        }]
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    pagination_class = CourseEnrollmentPagination

    required_scopes = ['grades:read']

    @verify_course_exists("Requested grade for unknown course {course}")
    def get(self, request, course_id=None):
        """
        Gets a course progress status.
        Args:
            request (Request): Django request object.
            course_id (string): URI element specifying the course location.
                                Can also be passed as a GET parameter instead.
        Return:
            A JSON serialized representation of the requesting user's current grade status.
        """
        username = request.GET.get('username')

        course_key = get_course_key(request, course_id)

        if username:
            # If there is a username passed, get grade for a single user
            with self._get_user_or_raise(request, course_key) as grade_user:
                return self._get_single_user_grade(grade_user, course_key)
        else:
            # If no username passed, get paginated list of grades for all users in course
            return self._get_user_grades(course_key)

    def _get_user_grades(self, course_key):
        """
        Get paginated grades for users in a course.
        Args:
            course_key (CourseLocator): The course to retrieve user grades for.

        Returns:
            A serializable list of grade responses
        """
        user_grades = []
        users = self._paginate_users(course_key)

        with bulk_course_grade_context(course_key, users):
            for user, course_grade, exc in CourseGradeFactory().iter(users, course_key=course_key):
                if not exc:
                    user_grades.append(self._serialize_user_grade(user, course_key, course_grade))

        return self.get_paginated_response(user_grades)


class CourseGradingPolicy(GradeViewMixin, ListAPIView):
    """
    **Use Case**

        Get the course grading policy.

    **Example requests**:

        GET /api/grades/v1/policy/courses/{course_id}/

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

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def _get_course(self, request, course_id):
        """
        Returns the course after parsing the id, checking access, and checking existence.
        """
        try:
            course_key = get_course_key(request, course_id)
        except InvalidKeyError:
            raise self.api_error(  # lint-amnesty, pylint: disable=raise-missing-from
                status_code=status.HTTP_400_BAD_REQUEST,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        if not has_access(request.user, 'staff', course_key):
            raise self.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The course does not exist.',
                error_code='user_or_course_does_not_exist',
            )

        course = modulestore().get_course(course_key, depth=0)
        if not course:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The course does not exist.',
                error_code='user_or_course_does_not_exist',
            )
        return course

    def get(self, request, course_id, *args, **kwargs):  # pylint: disable=arguments-differ
        course = self._get_course(request, course_id)
        return Response(GradingPolicySerializer(course.raw_grader, many=True).data)
