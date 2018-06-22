""" API v0 views. """
import logging

from django.contrib.auth import get_user_model
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from enrollment import data as enrollment_data
from student.models import CourseEnrollment
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes

log = logging.getLogger(__name__)
USER_MODEL = get_user_model()


@view_auth_classes()
class GradeViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    def _get_single_user_grade(self, request, course_key):
        """
        Returns a grade response for the user object corresponding to the request's 'username' parameter,
        or the current request.user if no 'username' was provided.
        Args:
            request (Request): django request object to check for username or request.user object
            course_key (CourseLocator): The course to retrieve user grades for.

        Returns:
            A serializable list of grade responses
        """
        if 'username' in request.GET:
            username = request.GET.get('username')
        else:
            username = request.user.username

        grade_user = USER_MODEL.objects.get(username=username)

        if not enrollment_data.get_course_enrollment(username, str(course_key)):
            raise CourseEnrollment.DoesNotExist

        course_grade = CourseGradeFactory().read(grade_user, course_key=course_key)
        return Response([self._make_grade_response(grade_user, course_key, course_grade)])

    def _get_user_grades(self, course_key):
        """
        Get paginated grades for users in a course.
        Args:
            course_key (CourseLocator): The course to retrieve user grades for.

        Returns:
            A serializable list of grade responses
        """
        enrollments_in_course = enrollment_data.get_user_enrollments(course_key)

        paged_enrollments = self.paginator.paginate_queryset(
            enrollments_in_course, self.request, view=self
        )
        users = (enrollment.user for enrollment in paged_enrollments)
        grades = CourseGradeFactory().iter(users, course_key=course_key)

        grade_responses = []
        for user, course_grade, exc in grades:
            if not exc:
                grade_responses.append(self._make_grade_response(user, course_key, course_grade))

        return Response(grade_responses)

    def _make_grade_response(self, user, course_key, course_grade):
        """
        Serialize a single grade to dict to use in Responses
        """
        return {
            'username': user.username,
            'email': user.email,
            'course_id': str(course_key),
            'passed': course_grade.passed,
            'percent': course_grade.percent,
            'letter_grade': course_grade.letter_grade,
        }

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser).
        """
        super(GradeViewMixin, self).perform_authentication(request)
        if request.user.is_anonymous():
            raise AuthenticationFailed


class CourseGradesView(GradeViewMixin, GenericAPIView):
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
    permission_classes = (IsUserInUrlOrStaff,)

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

        if not course_id:
            course_id = request.GET.get('course_id')

        # Validate course exists with provided course_id
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        if not CourseOverview.get_from_id_if_exists(course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=course_id),
                error_code='course_does_not_exist'
            )

        if username:
            # If there is a username passed, get grade for a single user
            try:
                return self._get_single_user_grade(request, course_key)
            except USER_MODEL.DoesNotExist:
                raise self.api_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    developer_message='The user matching the requested username does not exist.',
                    error_code='user_does_not_exist'
                )
            except CourseEnrollment.DoesNotExist:
                raise self.api_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    developer_message='The user matching the requested username is not enrolled in this course',
                    error_code='user_not_enrolled'
                )
        else:
            # If no username passed, get paginated list of grades for all users in course
            return self._get_user_grades(course_key)
