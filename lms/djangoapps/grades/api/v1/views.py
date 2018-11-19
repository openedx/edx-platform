""" API v0 views. """
import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import wraps

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from util.date_utils import to_timestamp

from courseware.courses import get_course_with_access
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from lms.djangoapps.grades.api.serializers import StudentGradebookEntrySerializer
from lms.djangoapps.grades.config.waffle import waffle_flags, WRITABLE_GRADEBOOK
from lms.djangoapps.grades.constants import ScoreDatabaseTableEnum
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.events import SUBSECTION_GRADE_CALCULATED, subsection_grade_calculated
from lms.djangoapps.grades.models import (
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride,
    PersistentSubsectionGradeOverrideHistory
)
from lms.djangoapps.grades.subsection_grade import CreateSubsectionGrade
from lms.djangoapps.grades.tasks import recalculate_subsection_grade_v3, are_grades_frozen
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups import cohorts
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from student.models import CourseEnrollment
from track.event_transaction_utils import (
    create_new_event_transaction_id,
    get_event_transaction_id,
    get_event_transaction_type,
    set_event_transaction_type
)
from xmodule.util.misc import get_default_short_labeler

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
    page_size = 50
    ordering = 'id'


class PaginatedAPIView(APIView):
    """
    An `APIView` class enhanced with the pagination methods of `GenericAPIView`.
    """
    # pylint: disable=attribute-defined-outside-init
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class GradeViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    def _get_single_user(self, request, course_key, user_id=None):
        """
        Returns a single USER_MODEL object corresponding to either the user_id provided, or if no id is provided,
        then the request's `username` parameter, or the current `request.user` if no `username` was provided.

        Args:
            request (Request): django request object to check for username or request.user object
            course_key (CourseLocator): The course to retrieve user grades for.
            user_id (int): Optional user id to fetch the user object for.

        Returns:
            A USER_MODEL object.

        Raises:
            USER_MODEL.DoesNotExist if no such user exists.
            CourseEnrollment.DoesNotExist if the user is not enrolled in the given course.
        """
        # May raise USER_MODEL.DoesNotExist if no user matching the given query exists.
        if user_id:
            grade_user = USER_MODEL.objects.get(id=user_id)
        elif 'username' in request.GET:
            grade_user = USER_MODEL.objects.get(username=request.GET.get('username'))
        else:
            grade_user = request.user

        # May raise CourseEnrollment.DoesNotExist if no enrollment exists for this user/course.
        _ = CourseEnrollment.objects.get(user=grade_user, course_id=course_key)

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

    def _iter_user_grades(self, course_key, course_enrollment_filter=None, related_models=None):
        """
        Args:
            course_key (CourseLocator): The course to retrieve grades for.
            course_enrollment_filter: Optional dictionary of keyword arguments to pass
            to `CourseEnrollment.filter()`.
            related_models: Optional list of related models to join to the CourseEnrollment table.

        Returns:
            An iterator of CourseGrade objects for users enrolled in the given course.
        """
        filter_kwargs = {
            'course_id': course_key,
            'is_active': True,
        }
        filter_kwargs.update(course_enrollment_filter or {})
        enrollments_in_course = CourseEnrollment.objects.filter(**filter_kwargs)
        if related_models:
            enrollments_in_course = enrollments_in_course.select_related(*related_models)

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
        for user, course_grade, exc in self._iter_user_grades(course_key):
            if not exc:
                user_grades.append(self._serialize_user_grade(user, course_key, course_grade))

        return self.get_paginated_response(user_grades)


class GradebookView(GradeViewMixin, PaginatedAPIView):
    """
    **Use Case**
        * Get course gradebook entries of a single user in a course,
        or of all users who are actively enrolled in a course.  The currently logged-in user may request
        all enrolled user's grades information if they are allowed.
    **Example Request**
        GET /api/grades/v1/gradebook/{course_id}/                       - Get gradebook entries for all users in course
        GET /api/grades/v1/gradebook/{course_id}/?username={username}   - Get grades for specific user in course
        GET /api/grades/v1/gradebook/{course_id}/?username_contains={username_contains}
        GET /api/grades/v1/gradebook/{course_id}/?cohort_id={cohort_id}
        GET /api/grades/v1/gradebook/{course_id}/?enrollment_mode={enrollment_mode}
    **GET Parameters**
        A GET request may include the following query parameters.
        * username:  (optional) A string representation of a user's username.
        * username_contains: (optional) A substring against which a case-insensitive substring filter will be performed
          on the USER_MODEL.username field.
        * cohort_id: (optional) The id of a cohort in this course.  If present, will return grades
          only for course enrollees who belong to that cohort.
        * enrollment_mode: (optional) The slug of an enrollment mode (e.g. "verified").  If present, will return grades
          only for course enrollees with the given enrollment mode.
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

    def _section_breakdown(self, course, course_grade):
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
        default_labeler = get_default_short_labeler(course)

        for chapter_location, section_data in course_grade.chapter_grades.items():
            for subsection_grade in section_data['sections']:
                default_short_label = default_labeler(subsection_grade.format)
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
                    'label': label_finder.get_label(subsection_grade.display_name) or default_short_label,
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
        breakdown, aggregates = self._section_breakdown(course, course_grade)

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
        course_key = get_course_key(request, course_id)
        course = get_course_with_access(request.user, 'staff', course_key, depth=None)

        if request.GET.get('username'):
            with self._get_user_or_raise(request, course_key) as grade_user:
                course_grade = CourseGradeFactory().read(grade_user, course)

            entry = self._gradebook_entry(grade_user, course, course_grade)
            serializer = StudentGradebookEntrySerializer(entry)
            return Response(serializer.data)
        else:
            filter_kwargs = {}
            related_models = []
            if request.GET.get('username_contains'):
                filter_kwargs['user__username__icontains'] = request.GET.get('username_contains')
                related_models.append('user')
            if request.GET.get('cohort_id'):
                cohort = cohorts.get_cohort_by_id(course_key, request.GET.get('cohort_id'))
                if cohort:
                    filter_kwargs['user__in'] = cohort.users.all()
                else:
                    filter_kwargs['user__in'] = []
            if request.GET.get('enrollment_mode'):
                filter_kwargs['mode'] = request.GET.get('enrollment_mode')

            user_grades = self._iter_user_grades(course_key, filter_kwargs, related_models)

            entries = []
            for user, course_grade, exc in user_grades:
                if not exc:
                    entries.append(self._gradebook_entry(user, course, course_grade))
            serializer = StudentGradebookEntrySerializer(entries, many=True)
            return self.get_paginated_response(serializer.data)


GradebookUpdateResponseItem = namedtuple('GradebookUpdateResponseItem', ['user_id', 'usage_id', 'success', 'reason'])


class GradebookBulkUpdateView(GradeViewMixin, PaginatedAPIView):
    """
    **Use Case**
        Creates `PersistentSubsectionGradeOverride` objects for multiple (user_id, usage_id)
        pairs in a given course, and invokes a Django signal to update subsection grades in
        an asynchronous celery task.

    **Example Request**
        POST /api/grades/v1/gradebook/{course_id}/bulk-update

    **POST Parameters**
        This endpoint does not accept any URL parameters.

    **Example POST Data**
        [
          {
            "user_id": 9,
            "usage_id": "block-v1:edX+DemoX+Demo_Course+type@sequential+block@basic_questions",
            "grade": {
              "earned_all_override": 11,
              "possible_all_override": 11,
              "earned_graded_override": 11,
              "possible_graded_override": 11
            }
          },
          {
            "user_id": 9,
            "usage_id": "block-v1:edX+DemoX+Demo_Course+type@sequential+block@advanced_questions",
            "grade": {
              "earned_all_override": 10,
              "possible_all_override": 15,
              "earned_graded_override": 9,
              "possible_graded_override": 12
            }
          }
        ]

    **POST Response Values**
        An HTTP 202 may be returned if a grade override was created for each of the requested (user_id, usage_id)
        pairs in the request data.
        An HTTP 403 may be returned if the `writable_gradebook` feature is not
        enabled for this course.
        An HTTP 404 may be returned for the following reasons:
            * The requested course_key is invalid.
            * No course corresponding to the requested key exists.
            * The requesting user is not enrolled in the requested course.
        An HTTP 422 may be returned if any of the requested (user_id, usage_id) pairs
        did not have a grade override created due to some exception.  A `reason` detailing the exception
        is provided with each response item.

    **Example successful POST Response**
        [
          {
            "user_id": 9,
            "usage_id": "some-requested-usage-id",
            "success": true,
            "reason": null
          },
          {
            "user_id": 9,
            "usage_id": "an-invalid-usage-id",
            "success": false,
            "reason": "<class 'opaque_keys.edx.locator.BlockUsageLocator'>: not-a-valid-usage-key"
          },
          {
            "user_id": 9,
            "usage_id": "a-valid-usage-key-that-doesn't-exist",
            "success": false,
            "reason": "a-valid-usage-key-that-doesn't-exist does not exist in this course"
          },
          {
            "user_id": 1234-I-DO-NOT-EXIST,
            "usage_id": "a-valid-usage-key",
            "success": false,
            "reason": "User matching query does not exist."
          }
        ]
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    required_scopes = ['grades:write']

    @verify_course_exists
    @verify_writable_gradebook_enabled
    def post(self, request, course_id):
        """
        Creates or updates `PersistentSubsectionGradeOverrides` for the (user_id, usage_key)
        specified in the request data.  The `SUBSECTION_OVERRIDE_CHANGED` signal is invoked
        after the grade override is created, which triggers a celery task to update the
        course and subsection grades for the specified user.
        """
        course_key = get_course_key(request, course_id)
        if are_grades_frozen(course_key):
            raise self.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='Grades are frozen for this course.',
                error_code='grades_frozen'
            )

        course = get_course_with_access(request.user, 'staff', course_key, depth=None)

        result = []

        for user_data in request.data:
            requested_user_id = user_data['user_id']
            requested_usage_id = user_data['usage_id']
            try:
                user = self._get_single_user(request, course_key, requested_user_id)
                usage_key = UsageKey.from_string(requested_usage_id)
            except (USER_MODEL.DoesNotExist, InvalidKeyError, CourseEnrollment.DoesNotExist) as exc:
                result.append(GradebookUpdateResponseItem(
                    user_id=requested_user_id,
                    usage_id=requested_usage_id,
                    success=False,
                    reason=text_type(exc)
                ))
                continue

            try:
                subsection_grade_model = PersistentSubsectionGrade.objects.get(
                    user_id=user.id,
                    course_id=course_key,
                    usage_key=usage_key
                )
            except PersistentSubsectionGrade.DoesNotExist:
                subsection = course.get_child(usage_key)
                if subsection:
                    subsection_grade_model = self._create_subsection_grade(user, course, subsection)
                else:
                    result.append(GradebookUpdateResponseItem(
                        user_id=requested_user_id,
                        usage_id=requested_usage_id,
                        success=False,
                        reason='usage_key {} does not exist in this course.'.format(usage_key)
                    ))
                    continue

            if subsection_grade_model:
                self._create_override(request.user, subsection_grade_model, **user_data['grade'])
                result.append(GradebookUpdateResponseItem(
                    user_id=user.id,
                    usage_id=text_type(usage_key),
                    success=True,
                    reason=None
                ))

        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if all((item.success for item in result)):
            status_code = status.HTTP_202_ACCEPTED

        return Response(
            [item._asdict() for item in result],
            status=status_code,
            content_type='application/json'
        )

    def _create_subsection_grade(self, user, course, subsection):
        course_data = CourseData(user, course=course)
        subsection_grade = CreateSubsectionGrade(subsection, course_data.structure, {}, {})
        return subsection_grade.update_or_create_model(user, force_update_subsections=True)

    def _create_override(self, request_user, subsection_grade_model, **override_data):
        """
        Helper method to create a `PersistentSubsectionGradeOverride` object
        and send a `SUBSECTION_OVERRIDE_CHANGED` signal.
        """
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(
            grade=subsection_grade_model,
            defaults=self._clean_override_data(override_data),
        )

        _ = PersistentSubsectionGradeOverrideHistory.objects.create(
            override_id=override.id,
            user=request_user,
            feature=PersistentSubsectionGradeOverrideHistory.GRADEBOOK,
            action=PersistentSubsectionGradeOverrideHistory.CREATE_OR_UPDATE,
        )

        set_event_transaction_type(SUBSECTION_GRADE_CALCULATED)
        create_new_event_transaction_id()

        recalculate_subsection_grade_v3.apply(
            kwargs=dict(
                user_id=subsection_grade_model.user_id,
                anonymous_user_id=None,
                course_id=text_type(subsection_grade_model.course_id),
                usage_id=text_type(subsection_grade_model.usage_key),
                only_if_higher=False,
                expected_modified_time=to_timestamp(override.modified),
                score_deleted=False,
                event_transaction_id=unicode(get_event_transaction_id()),
                event_transaction_type=unicode(get_event_transaction_type()),
                score_db_table=ScoreDatabaseTableEnum.overrides,
                force_update_subsections=True,
            )
        )
        # Emit events to let our tracking system to know we updated subsection grade
        subsection_grade_calculated(subsection_grade_model)

    def _clean_override_data(self, override_data):
        """
        Helper method to strip any grade override field names that won't work
        as defaults when calling PersistentSubsectionGradeOverride.update_or_create().
        """
        allowed_fields = {
            'earned_all_override',
            'possible_all_override',
            'earned_graded_override',
            'possible_graded_override',
        }
        stripped_data = {}
        for field in override_data.keys():
            if field in allowed_fields:
                stripped_data[field] = override_data[field]
        return stripped_data
