""" API v0 views. """
import logging
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from six import text_type

from courseware.courses import get_course_with_access
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from enrollment import data as enrollment_data
from lms.djangoapps.grades.api.serializers import StudentGradebookEntrySerializer
from lms.djangoapps.grades.config.waffle import waffle_flags, WRITABLE_GRADEBOOK
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from student.models import CourseEnrollment


log = logging.getLogger(__name__)
USER_MODEL = get_user_model()


def get_course_key(request, course_id=None):
    if not course_id:
        return CourseKey.from_string(request.GET.get('course_id'))
    return CourseKey.from_string(course_id)


def verify_course_exists(view_func):
    """
    A decorator to wrap a view function that takes `course_key` as a parameter.

    Raises:
        An API error if the `course_key` is invalid, or if no `CourseOverview` exists for the given key.
    """
    @wraps(view_func)
    def wrapped_function(self, request, **kwargs):
        """
        Wraps the given view_function.
        """
        try:
            course_key = get_course_key(request, kwargs.get('course_id'))
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        if not CourseOverview.get_from_id_if_exists(course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=text_type(course_key)),
                error_code='course_does_not_exist'
            )

        return view_func(self, request, **kwargs)
    return wrapped_function


def verify_writable_gradebook_enabled(view_func):
    """
    A decorator to wrap a view function that takes `course_key` as a parameter.

    Raises:
        A 403 API error if the writable gradebook feature is not enabled for the given course.
    """
    @wraps(view_func)
    def wrapped_function(self, request, **kwargs):
        """
        Wraps the given view function.
        """
        course_key = get_course_key(request, kwargs.get('course_id'))
        if not waffle_flags()[WRITABLE_GRADEBOOK].is_enabled(course_key):
            raise self.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The writable gradebook feature is not enabled for this course.',
                error_code='feature_not_enabled'
            )
        return view_func(self, request, **kwargs)
    return wrapped_function


class CourseEnrollmentPagination(CursorPagination):
    """
    Paginates over CourseEnrollment objects.
    """
    page_size = 25
    ordering = 'created'


class GradeViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    def _get_single_user(self, request, course_key):
        """
        Returns a single USER_MODEL object corresponding to the request's `username` parameter,
        or the current `request.user` if no `username` was provided.
        Args:
            request (Request): django request object to check for username or request.user object
            course_key (CourseLocator): The course to retrieve user grades for.

        Returns:
            A USER_MODEL object.

        Raises:
            USER_MODEL.DoesNotExist if no such user exists.
            CourseEnrollment.DoesNotExist if the user is not enrolled in the given course.
        """
        if 'username' in request.GET:
            username = request.GET.get('username')
        else:
            username = request.user.username

        grade_user = USER_MODEL.objects.get(username=username)

        if not enrollment_data.get_course_enrollment(username, text_type(course_key)):
            raise CourseEnrollment.DoesNotExist

        return grade_user

    @contextmanager
    def _get_user_or_raise(self, request, course_key):
        """
        Raises an API error if the username specified by the request does not exist, or if the
        user is not enrolled in the given course.
        Args:
            request (Request): django request object to check for username or request.user object
            course_key (CourseLocator): The course to retrieve user grades for.

        Yields:
            A USER_MODEL object.
        """
        try:
            yield self._get_single_user(request, course_key)
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

    def _get_single_user_grade(self, grade_user, course_key):
        """
        Returns a grade response for the user object corresponding to the request's 'username' parameter,
        or the current request.user if no 'username' was provided.
        Args:
            request (Request): django request object to check for username or request.user object
            course_key (CourseLocator): The course to retrieve user grades for.

        Returns:
            A serializable list of grade responses
        """
        course_grade = CourseGradeFactory().read(grade_user, course_key=course_key)
        return Response([self._serialize_user_grade(grade_user, course_key, course_grade)])

    def _iter_user_grades(self, course_key):
        """
        Args:
            course_key (CourseLocator): The course to retrieve grades for.

        Returns:
            An iterator of CourseGrade objects for users enrolled in the given course.
        """
        enrollments_in_course = CourseEnrollment.objects.filter(
            course_id=course_key,
            is_active=True
        )

        paged_enrollments = self.paginate_queryset(enrollments_in_course)
        users = (enrollment.user for enrollment in paged_enrollments)
        grades = CourseGradeFactory().iter(users, course_key=course_key)

        for user, course_grade, exc in grades:
            yield user, course_grade, exc

    def _serialize_user_grade(self, user, course_key, course_grade):
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
        if request.user.is_anonymous:
            raise AuthenticationFailed


class SubsectionLabelFinder(object):
    """
    Finds the grader label (a short string identifying the section) of a graded section.
    """
    def __init__(self, course_grade):
        """
        Args:
            course_grade: A CourseGrade object.
        """
        self.section_summaries = [section for section in course_grade.summary.get('section_breakdown', [])]

    def _get_subsection_summary(self, display_name):
        """
        Given a subsection's display_name and a breakdown of section grades from CourseGrade.summary,
        return the summary data corresponding to the subsection with this display_name.
        """
        for index, section in enumerate(self.section_summaries):
            if display_name.lower() in section['detail'].lower():
                return index, section
        return -1, None

    def get_label(self, display_name):
        """
        Returns the grader short label corresponding to the display_name, or None
        if no match was found.
        """
        section_index, summary = self._get_subsection_summary(display_name)
        if summary:
            # It's possible that two subsections/assignments would have the same display name.
            # since the grade summary and chapter_grades data are presumably in a sorted order,
            # we'll take the first matching section summary and remove it from the pool of
            # section_summaries.
            self.section_summaries.pop(section_index)
            return summary['label']


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
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    pagination_class = CourseEnrollmentPagination

    required_scopes = ['grades:read']

    @verify_course_exists
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
            with self._get_user_or_raise(request, course_id) as grade_user:
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
        for user, course_grade, exc in self._iter_user_grades(course_key):
            if not exc:
                user_grades.append(self._serialize_user_grade(user, course_key, course_grade))

        return self.get_paginated_response(user_grades)


class GradebookView(GradeViewMixin, GenericAPIView):
    """
    **Use Case**
        * Get course gradebook entries of a single user in a course,
        or of all users who are enrolled in a course.  The currently logged-in user may request
        all enrolled user's grades information if they are allowed.
    **Example Request**
        GET /api/grades/v1/gradebook/{course_id}/                       - Get gradebook entries for all users in course
        GET /api/grades/v1/gradebook/{course_id}/?username={username}   - Get grades for specific user in course
    **GET Parameters**
        A GET request may include the following query parameters.
        * username:  (optional) A string representation of a user's username.
    **GET Response Values**
        If the request for gradebook data is successful,
        an HTTP 200 "OK" response is returned.
        The HTTP 200 response for a single has the following values:
        * course_id: A string representation of a Course ID.
        * email: A string representation of a user's email.
        * user_id: The user's integer id.
        * username: A string representation of a user's username passed in the request.
        * full_name: A string representation of the user's full name.
        * passed: Boolean representing whether the course has been
                  passed according to the course's grading policy.
        * percent: A float representing the overall grade for the course
        * letter_grade: A letter grade as defined in grading policy (e.g. 'A' 'B' 'C' for 6.002x) or None
        * progress_page_url: A link to the user's progress page.
        * section_breakdown: A list of subsection grade details, as specified below.
        * aggregates: A dict containing earned and possible scores (floats), broken down by subsection type
                      (e.g. "Exam", "Homework", "Lab").

        A response for all user's grades in the course is paginated, and contains "count", "next" and "previous"
        keys, along with the actual data contained in a "results" list.

        An HTTP 404 may be returned for the following reasons:
            * The requested course_key is invalid.
            * No course corresponding to the requested key exists.
            * No user corresponding to the requested username exists.
            * The requested user is not enrolled in the requested course.

        An HTTP 403 may be returned if the `writable_gradebook` feature is not
        enabled for this course.
    **Example GET Response**
        {
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "email": "staff@example.com",
            "user_id": 9,
            "username": "staff",
            "full_name": "",
            "passed": false,
            "percent": 0.36,
            "letter_grade": null,
            "progress_page_url": "/courses/course-v1:edX+DemoX+Demo_Course/progress/9/",
            "section_breakdown": [
                {
                    "are_grades_published": true,
                    "auto_grade": false,
                    "category": null,
                    "chapter_name": "Introduction",
                    "comment": "",
                    "detail": "",
                    "displayed_value": "0.00",
                    "is_graded": false,
                    "grade_description": "(0.00/0.00)",
                    "is_ag": false,
                    "is_average": false,
                    "is_manually_graded": false,
                    "label": null,
                    "letter_grade": null,
                    "module_id": "block-v1:edX+DemoX+Demo_Course+type@sequential+block@edx_introduction",
                    "percent": 0.0,
                    "score_earned": 0.0,
                    "score_possible": 0.0,
                    "section_block_id": "block-v1:edX+DemoX+Demo_Course+type@chapter+block@abcdefgh123",
                    "subsection_name": "Demo Course Overview"
                },
            ],
            "aggregates": {
                "Exam": {
                  "score_possible": 6.0,
                  "score_earned": 0.0
                },
                "Homework": {
                  "score_possible": 16.0,
                  "score_earned": 10.0
                }
            }
        }
    **Paginated GET response**
        When requesting gradebook entries for all users, the response is paginated and contains the following values:
        * count: The total number of user gradebook entries for this course.
        * next: The URL containing the next page of data.
        * previous: The URL containing the previous page of data.
        * results: A list of user gradebook entries, structured as above.

    Note: It's important that `GradeViewMixin` is the first inherited class here, so that
    self.api_error returns error responses as expected.
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    pagination_class = CourseEnrollmentPagination

    required_scopes = ['grades:read']

    def _section_breakdown(self, course_grade):
        """
        Given a course_grade, returns a list of grade data broken down by subsection
        and a dictionary containing aggregate grade data by subsection format for the course.

        Args:
            course_grade: A CourseGrade object.
        """
        breakdown = []
        aggregates = defaultdict(lambda: defaultdict(float))

        # TODO: https://openedx.atlassian.net/browse/EDUCATOR-3559
        # Fields we may not need:
        # ['are_grades_published', 'auto_grade', 'comment', 'detail', 'is_ag', 'is_average', 'is_manually_graded']
        # Some fields should be renamed:
        # 'displayed_value' should maybe be 'description_percent'
        # 'grade_description' should be 'description_ratio'

        label_finder = SubsectionLabelFinder(course_grade)

        for chapter_location, section_data in course_grade.chapter_grades.items():
            for subsection_grade in section_data['sections']:
                breakdown.append({
                    'are_grades_published': True,
                    'auto_grade': False,
                    'category': subsection_grade.format,
                    'chapter_name': section_data['display_name'],
                    'comment': '',
                    'detail': '',
                    'displayed_value': '{:.2f}'.format(subsection_grade.percent_graded),
                    'is_graded': subsection_grade.graded,
                    'grade_description': '({earned:.2f}/{possible:.2f})'.format(
                        earned=subsection_grade.graded_total.earned,
                        possible=subsection_grade.graded_total.possible,
                    ),
                    'is_ag': False,
                    'is_average': False,
                    'is_manually_graded': False,
                    'label': label_finder.get_label(subsection_grade.display_name),
                    'letter_grade': course_grade.letter_grade,
                    'module_id': text_type(subsection_grade.location),
                    'percent': subsection_grade.percent_graded,
                    'score_earned': subsection_grade.graded_total.earned,
                    'score_possible': subsection_grade.graded_total.possible,
                    'section_block_id': text_type(chapter_location),
                    'subsection_name': subsection_grade.display_name,
                })
                if subsection_grade.graded and subsection_grade.graded_total.possible > 0:
                    aggregates[subsection_grade.format]['score_earned'] += subsection_grade.graded_total.earned
                    aggregates[subsection_grade.format]['score_possible'] += subsection_grade.graded_total.possible

        return breakdown, aggregates

    def _gradebook_entry(self, user, course, course_grade):
        """
        Returns a dictionary of course- and subsection-level grade data for
        a given user in a given course.

        Args:
            user: A User object.
            course: A Course Descriptor object.
            course_grade: A CourseGrade object.
        """
        user_entry = self._serialize_user_grade(user, course.id, course_grade)
        breakdown, aggregates = self._section_breakdown(course_grade)

        user_entry['section_breakdown'] = breakdown
        user_entry['aggregates'] = aggregates
        user_entry['progress_page_url'] = reverse(
            'student_progress',
            kwargs=dict(course_id=text_type(course.id), student_id=user.id)
        )
        user_entry['user_id'] = user.id
        user_entry['full_name'] = user.get_full_name()

        return user_entry

    @verify_course_exists
    @verify_writable_gradebook_enabled
    def get(self, request, course_id):
        """
        Returns a gradebook entry/entries (i.e. both course and subsection-level grade data)
        for all users enrolled in a course, or a single user enrolled in a course
        if a `username` parameter is provided.

        Args:
            request: A Django request object.
            course_id: A string representation of a CourseKey object.
        """
        username = request.GET.get('username')
        course_key = get_course_key(request, course_id)
        course = get_course_with_access(request.user, 'staff', course_key, depth=None)

        if username:
            with self._get_user_or_raise(request, course_id) as grade_user:
                course_grade = CourseGradeFactory().read(grade_user, course)

            entry = self._gradebook_entry(grade_user, course, course_grade)
            serializer = StudentGradebookEntrySerializer(entry)
            return Response(serializer.data)
        else:
            # list gradebook data for all course enrollees
            entries = []
            for user, course_grade, exc in self._iter_user_grades(course_key):
                if not exc:
                    entries.append(self._gradebook_entry(user, course, course_grade))
            serializer = StudentGradebookEntrySerializer(entries, many=True)
            return self.get_paginated_response(serializer.data)
