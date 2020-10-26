"""
Defines an endpoint for gradebook data related to a course.
"""
import logging
from collections import namedtuple
from contextlib import contextmanager
from functools import wraps

from django.urls import reverse
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from util.date_utils import to_timestamp

from courseware.courses import get_course_by_id
from lms.djangoapps.grades.api.serializers import StudentGradebookEntrySerializer, SubsectionGradeResponseSerializer
from lms.djangoapps.grades.api.v1.utils import (
    USER_MODEL,
    CourseEnrollmentPagination,
    GradeViewMixin,
    PaginatedAPIView,
    get_course_key,
    verify_course_exists
)
from lms.djangoapps.grades.config.waffle import WRITABLE_GRADEBOOK, waffle_flags
from lms.djangoapps.grades.constants import ScoreDatabaseTableEnum
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.events import SUBSECTION_GRADE_CALCULATED, subsection_grade_calculated
from lms.djangoapps.grades.models import (
    PersistentCourseGrade,
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride,
    PersistentSubsectionGradeOverrideHistory,
)
from lms.djangoapps.grades.subsection_grade import CreateSubsectionGrade
from lms.djangoapps.grades.tasks import are_grades_frozen, recalculate_subsection_grade_v3
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx.core.djangoapps.course_groups import cohorts
from openedx.core.djangoapps.util.forms import to_bool
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.lib.cache_utils import request_cached
from student.auth import has_course_author_access
from student.models import CourseEnrollment
from student.roles import BulkRoleCache
from track.event_transaction_utils import (
    create_new_event_transaction_id,
    get_event_transaction_id,
    get_event_transaction_type,
    set_event_transaction_type
)
from xmodule.modulestore.django import modulestore
from xmodule.util.misc import get_default_short_labeler

log = logging.getLogger(__name__)


@contextmanager
def bulk_gradebook_view_context(course_key, users):
    """
    Prefetches all course and subsection grades in the given course for the given
    list of users, also, fetch all the score relavant data,
    storing the result in a RequestCache and deleting grades on context exit.
    """
    PersistentSubsectionGrade.prefetch(course_key, users)
    PersistentCourseGrade.prefetch(course_key, users)
    CourseEnrollment.bulk_fetch_enrollment_states(users, course_key)
    cohorts.bulk_cache_cohorts(course_key, users)
    BulkRoleCache.prefetch(users)
    yield
    PersistentSubsectionGrade.clear_prefetched_data(course_key)
    PersistentCourseGrade.clear_prefetched_data(course_key)


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


@view_auth_classes()
class BaseCourseView(DeveloperErrorViewMixin, GenericAPIView):
    """
    A base class for course info APIs.
    TODO: https://openedx.atlassian.net/browse/EDUCATOR-3755
    This whole thing is duplicated from cms/djangoapps/contentstore
    """
    @contextmanager
    def get_course(self, request, course_key):
        """
        Context manager that yields a course, given a request and course_key.
        """
        store = modulestore()
        with store.bulk_operations(course_key):
            course = store.get_course(course_key, depth=self._required_course_depth(request))
            yield course

    @staticmethod
    def _required_course_depth(request):
        """
        Returns how far deep we need to go into the course tree to
        get all of the information required.  Will use entire tree if the request's
        `all` param is truthy, otherwise goes to depth of 2 (subsections).
        """
        all_requested = get_bool_param(request, 'all', False)
        if all_requested:
            return None
        return 2

    @classmethod
    @request_cached()
    def _get_visible_subsections(cls, course):
        """
        Returns a list of all visible subsections for a course.
        """
        _, visible_sections = cls._get_sections(course)
        visible_subsections = []
        for section in visible_sections:
            visible_subsections.extend(cls._get_visible_children(section))
        return visible_subsections

    @classmethod
    @request_cached()
    def _get_sections(cls, course):
        """
        Returns all sections in the course.
        """
        return cls._get_all_children(course)

    @classmethod
    def _get_all_children(cls, parent):
        """
        Returns all child nodes of the given parent.
        """
        store = modulestore()
        children = [store.get_item(child_usage_key) for child_usage_key in cls._get_children(parent)]
        visible_children = [
            c for c in children
            if not c.visible_to_staff_only and not c.hide_from_toc
        ]
        return children, visible_children

    @classmethod
    def _get_visible_children(cls, parent):
        """
        Returns only the visible children of the given parent.
        """
        _, visible_chidren = cls._get_all_children(parent)
        return visible_chidren

    @classmethod
    def _get_children(cls, parent):
        """
        Returns the value of the 'children' attribute of a node.
        """
        if not hasattr(parent, 'children'):
            return []
        else:
            return parent.children


def get_bool_param(request, param_name, default):
    """
    Given a request, parameter name, and default value, returns
    either a boolean value or the default.
    """
    param_value = request.query_params.get(param_name, None)
    bool_value = to_bool(param_value)
    if bool_value is None:
        return default
    else:
        return bool_value


def course_author_access_required(view):
    """
    Ensure the user making the API request has course author access to the given course.

    This decorator parses the course_id parameter, checks course access, and passes
    the parsed course_key to the view as a parameter. It will raise a
    403 error if the user does not have author access.

    Usage::
        @course_author_access_required
        def my_view(request, course_key):
            # Some functionality ...
    """
    def _wrapper_view(self, request, course_id, *args, **kwargs):
        """
        Checks for course author access for the given course by the requesting user.
        Calls the view function if has access, otherwise raises a 403.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_course_author_access(request.user, course_key):
            raise DeveloperErrorViewMixin.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The requesting user does not have course author permissions.',
                error_code='user_permissions',
            )
        return view(self, request, course_key, *args, **kwargs)
    return _wrapper_view


class CourseGradingView(BaseCourseView):
    """
    Returns information about assignments and assignment types for a course.
    **Example Requests**

        GET /api/grades/v1/gradebook/{course_id}/grading-info

    **GET Parameters**

        A GET request may include the following parameters.

        * graded_only (boolean) - If true, only returns subsection data for graded subsections (defaults to False).

    **GET Response Values**

        The HTTP 200 response has the following values.

        * assignment_types - A dictionary keyed by the assignment type name with the following values:
            * min_count - The minimum number of required assignments of this type.
            * weight - The weight assigned to this assignment type for course grading.
            * type - The name of the assignment type.
            * drop_count - The maximum number of assignments of this type that can be dropped.
            * short_label - The short label prefix used for short labels of assignments of this type (e.g. 'HW').

        * subsections - A list of subsections contained in this course.
            * module_id - The string version of this subsection's location.
            * display_name - The display name of this subsection.
            * graded - Boolean indicating whether this subsection is graded (for at least one user in the course).
            * short_label - A short label for graded assignments (e.g. 'HW 01').
            * assignment_type - The assignment type of this subsection (for graded assignments only).

    """
    @course_author_access_required
    def get(self, request, course_key):
        """
        Returns grading information (which subsections are graded, assignment types) for
        the requested course.
        """
        graded_only = get_bool_param(request, 'graded_only', False)

        with self.get_course(request, course_key) as course:
            results = {
                'assignment_types': self._get_assignment_types(course),
                'subsections': self._get_subsections(course, graded_only),
                'grades_frozen': are_grades_frozen(course_key),
            }
            return Response(results)

    def _get_assignment_types(self, course):
        """
        Helper function that returns a serialized dict of assignment types
        for the given course.
        Args:
            course - A course object.
        """
        serialized_grading_policies = {}
        for grader, assignment_type, weight in course.grader.subgraders:
            serialized_grading_policies[assignment_type] = {
                'type': assignment_type,
                'short_label': grader.short_label,
                'min_count': grader.min_count,
                'drop_count': grader.drop_count,
                'weight': weight,
            }
        return serialized_grading_policies

    def _get_subsections(self, course, graded_only=False):
        """
        Helper function that returns a list of subsections contained in the given course.
        Args:
            course - A course object.
            graded_only - If true, returns only graded subsections (defaults to False).
        """
        subsections = []
        short_labeler = get_default_short_labeler(course)
        for subsection in self._get_visible_subsections(course):
            if graded_only and not subsection.graded:
                continue

            short_label = None
            if subsection.graded:
                short_label = short_labeler(subsection.format)

            subsections.append({
                'assignment_type': subsection.format,
                'graded': subsection.graded,
                'short_label': short_label,
                'module_id': text_type(subsection.location),
                'display_name': subsection.display_name,
            })
        return subsections


@view_auth_classes()
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

    pagination_class = CourseEnrollmentPagination

    def _section_breakdown(self, course, graded_subsections, course_grade):
        """
        Given a course_grade and a list of graded subsections for a given course,
        returns a list of grade data broken down by subsection.

        Args:
            course: A Course Descriptor object
            graded_subsections: A list of graded subsection objects in the given course.
            course_grade: A CourseGrade object.
        """
        breakdown = []
        default_labeler = get_default_short_labeler(course)

        for subsection in graded_subsections:
            subsection_grade = course_grade.subsection_grade(subsection.location)
            short_label = default_labeler(subsection_grade.format)

            attempted = False
            score_earned = 0
            score_possible = 0

            # For ZeroSubsectionGrades, we don't want to crawl the subsection's
            # subtree to find the problem scores specific to this user
            # (ZeroSubsectionGrade.attempted_graded is always False).
            # We've already fetched the whole course structure in a non-user-specific way
            # when creating `graded_subsections`.  Looking at the problem scores
            # specific to this user (the user in `course_grade.user`) would require
            # us to re-fetch the user-specific course structure from the modulestore,
            # which is a costly operation.  So we only drill into the `graded_total`
            # attribute if the user has attempted this graded subsection, or if there
            # has been a grade override applied.
            if subsection_grade.attempted_graded or subsection_grade.override:
                attempted = True
                score_earned = subsection_grade.graded_total.earned
                score_possible = subsection_grade.graded_total.possible

            # TODO: https://openedx.atlassian.net/browse/EDUCATOR-3559 -- Some fields should be renamed, others removed:
            # 'displayed_value' should maybe be 'description_percent'
            # 'grade_description' should be 'description_ratio'
            breakdown.append({
                'attempted': attempted,
                'category': subsection_grade.format,
                'is_graded': subsection_grade.graded,
                'label': short_label,
                'letter_grade': course_grade.letter_grade,
                'module_id': text_type(subsection_grade.location),
                'percent': subsection_grade.percent_graded,
                'score_earned': score_earned,
                'score_possible': score_possible,
                'subsection_name': subsection_grade.display_name,
            })
        return breakdown

    def _gradebook_entry(self, user, course, graded_subsections, course_grade):
        """
        Returns a dictionary of course- and subsection-level grade data for
        a given user in a given course.

        Args:
            user: A User object.
            course: A Course Descriptor object.
            graded_subsections: A list of graded subsections in the given course.
            course_grade: A CourseGrade object.
        """
        user_entry = self._serialize_user_grade(user, course.id, course_grade)
        breakdown = self._section_breakdown(course, graded_subsections, course_grade)

        user_entry['section_breakdown'] = breakdown
        user_entry['progress_page_url'] = reverse(
            'student_progress',
            kwargs=dict(course_id=text_type(course.id), student_id=user.id)
        )
        user_entry['user_id'] = user.id
        user_entry['full_name'] = user.get_full_name()

        return user_entry

    @verify_course_exists
    @verify_writable_gradebook_enabled
    @course_author_access_required
    def get(self, request, course_key):
        """
        Returns a gradebook entry/entries (i.e. both course and subsection-level grade data)
        for all users enrolled in a course, or a single user enrolled in a course
        if a `username` parameter is provided.

        Args:
            request: A Django request object.
            course_key: The edx course opaque key of a course object.
        """
        course = get_course_by_id(course_key, depth=None)

        # We fetch the entire course structure up-front, and use this when iterating
        # over users to determine their subsection grades.  We purposely avoid fetching
        # the user-specific course structure for each user, because that is very expensive.
        course_data = CourseData(user=None, course=course)
        graded_subsections = list(graded_subsections_for_course(course_data.collected_structure))

        if request.GET.get('username'):
            with self._get_user_or_raise(request, course_key) as grade_user:
                course_grade = CourseGradeFactory().read(grade_user, course)

            entry = self._gradebook_entry(grade_user, course, graded_subsections, course_grade)
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

            entries = []
            users = self._paginate_users(course_key, filter_kwargs, related_models)

            with bulk_gradebook_view_context(course_key, users):
                for user, course_grade, exc in CourseGradeFactory().iter(
                    users, course_key=course_key, collected_block_structure=course_data.collected_structure
                ):
                    if not exc:
                        entries.append(self._gradebook_entry(user, course, graded_subsections, course_grade))

            serializer = StudentGradebookEntrySerializer(entries, many=True)
            return self.get_paginated_response(serializer.data)


def graded_subsections_for_course(course_structure):
    """
    Given a course block structure, yields the subsections of the course that are graded.
    Args:
        course_structure: A course structure object.  Not user-specific.
    """
    for chapter_key in course_structure.get_children(course_structure.root_block_usage_key):
        for subsection_key in course_structure.get_children(chapter_key):
            subsection = course_structure[subsection_key]
            if subsection.graded:
                yield subsection


GradebookUpdateResponseItem = namedtuple('GradebookUpdateResponseItem', ['user_id', 'usage_id', 'success', 'reason'])


@view_auth_classes()
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

    @verify_course_exists
    @verify_writable_gradebook_enabled
    @course_author_access_required
    def post(self, request, course_key):
        """
        Creates or updates `PersistentSubsectionGradeOverrides` for the (user_id, usage_key)
        specified in the request data.  The `SUBSECTION_OVERRIDE_CHANGED` signal is invoked
        after the grade override is created, which triggers a celery task to update the
        course and subsection grades for the specified user.
        """
        if are_grades_frozen(course_key):
            raise self.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='Grades are frozen for this course.',
                error_code='grades_frozen'
            )

        course = get_course_by_id(course_key, depth=None)

        result = []

        for user_data in request.data:
            requested_user_id = user_data['user_id']
            requested_usage_id = user_data['usage_id']
            try:
                user = self._get_single_user(request, course_key, requested_user_id)
                usage_key = UsageKey.from_string(requested_usage_id)
            except (USER_MODEL.DoesNotExist, InvalidKeyError, CourseEnrollment.DoesNotExist) as exc:
                self._log_update_result(request.user, requested_user_id, requested_usage_id, success=False)
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
                    self._log_update_result(request.user, requested_user_id, requested_usage_id, success=False)
                    result.append(GradebookUpdateResponseItem(
                        user_id=requested_user_id,
                        usage_id=requested_usage_id,
                        success=False,
                        reason='usage_key {} does not exist in this course.'.format(usage_key)
                    ))
                    continue

            if subsection_grade_model:
                override = self._create_override(request.user, subsection_grade_model, **user_data['grade'])

                self._log_update_result(
                    request.user, requested_user_id, requested_usage_id, subsection_grade_model, override, True
                )
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
        override = PersistentSubsectionGradeOverride.update_or_create_override(
            requesting_user=request_user,
            subsection_grade_model=subsection_grade_model,
            feature=PersistentSubsectionGradeOverrideHistory.GRADEBOOK,
            **override_data
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
        return override

    @staticmethod
    def _log_update_result(
        request_user,
        user_id, usage_id,
        subsection_grade_model=None,
        subsection_grade_override=None,
        success=False
    ):

        log.info(
            'Grades: Bulk_Update, UpdatedByUser: %s, User: %s, Usage: %s, Grade: %s, GradeOverride: %s, Success: %s',
            request_user.id,
            user_id,
            usage_id,
            subsection_grade_model,
            subsection_grade_override,
            success
        )


@view_auth_classes()
class SubsectionGradeView(GradeViewMixin, APIView):
    """
    **Use Case**
        * This api is to get information about a users original grade for a subsection.
        It also exposes any overrides that now replace the original grade and a history of user changes
        with time stamps of all changes.
    **Example Request**
        GET /api/grades/v1/subsection/{subsection_id}/?user_id={user_id}
    **GET Parameters**
        A GET request may include the following query parameters.
        * user_id: (required) An integer represenation of a user
    **GET Response Values**
        If the request for subsection grade data is successful,
        an HTTP 200 "OK" response is returned.
        The HTTP 200 response has the following values:
        * subsection_id: A string representation of the usage_key for a course subsection
        * user_id: The user's integer id
        * course_id: A string representation of a Course ID.
        * original_grade: An object representation of a users original grade containing:
            * earned_all: The float score a user earned for all graded and not graded problems
            * possible_all: The float highest score a user can earn for all graded and not graded problems
            * earned_graded: The float score a user earned for only graded probles
            * possible_graded: The float highest score a user can earn for only graded problems
        * override: An object representation of an over ride for a user's subsection grade containing:
            * earned_all_override: The float overriden score a user earned for all graded and not graded problems
            * possible_all_override: The float overriden highest score a user can earn for all graded
              and not graded problems
            * earned_graded_override: The float overriden grade a user earned for only graded problems
            * possible_graded_override: The float overriden highest possible grade a user can earn
              for only graded problems
        * history: A list of history objects that contain
            * user: The string representation of the user who was responsible for overriding the grade
            * comments: A string comment about why that person changed the grade
            * created: The date timestamp the grade was changed
            * feature: The string representation of the feature through which the grade was overrriden
            * action: The string representation of the CRUD action the override did

        An HTTP 404 may be returned for the following reasons:
            * The requested subsection_id is invalid.
            * The requested user_id is invalid.
            * NOTE: if you pass in a valid subsection_id and a valid user_id with no data representation in the DB
              then you will still recieve a 200 with a response with 'original_grade', 'override' and 'course_id'
              set to None and the 'history' list will be empty.

    **Example GET Response**
        {
            "subsection_id": "block-v1:edX+DemoX+Demo_Course+type@sequential+block@basic_questions",
            "user_id": 2,
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "original_grade": {
                "earned_all": 0,
                "possible_all": 11,
                "earned_graded": 8,
                "possible_graded": 11
            },
            "override": {
                "earned_all_override": null,
                "possible_all_override": null,
                "earned_graded_override": 8,
                "possible_graded_override": null
            },
            "history": [
                {
                    "user": "edx",
                    "comments": null,
                    "created": "2018-12-03T18:52:36.087134Z",
                    "feature": "GRADEBOOK",
                    "action": "CREATEORUPDATE"
                },
                {
                    "user": "edx",
                    "comments": null,
                    "created": "2018-12-03T20:41:02.507685Z",
                    "feature": "GRADEBOOK",
                    "action": "CREATEORUPDATE"
                },
                {
                    "user": "edx",
                    "comments": null,
                    "created": "2018-12-03T20:46:08.933387Z",
                    "feature": "GRADEBOOK",
                    "action": "CREATEORUPDATE"
                }
            ]
        }
    """

    def get(self, request, subsection_id):
        """
        Returns subection grade data, override grade data and a history of changes made to
        a specific users specific subsection grade.

        Args:
            subsection_id: String representation of a usage_key, which is an opaque key of
            a persistant subection grade.
            user_id: An integer represenation of a user

        """
        try:
            usage_key = UsageKey.from_string(subsection_id)
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='Invalid UsageKey',
                error_code='invalid_usage_key'
            )

        if not has_course_author_access(request.user, usage_key.course_key):
            raise DeveloperErrorViewMixin.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The requesting user does not have course author permissions.',
                error_code='user_permissions',
            )

        try:
            user_id = int(request.GET.get('user_id'))
        except ValueError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='Invalid UserID',
                error_code='invalid_user_id'
            )

        try:
            original_grade = PersistentSubsectionGrade.read_grade(user_id, usage_key)
        except PersistentSubsectionGrade.DoesNotExist:
            results = SubsectionGradeResponseSerializer({
                'original_grade': None,
                'override': None,
                'history': [],
                'subsection_id': usage_key,
                'user_id': user_id,
                'course_id': None,
            })

            return Response(results.data)

        try:
            override = original_grade.override
            history = PersistentSubsectionGradeOverrideHistory.objects.filter(override_id=override.id)
        except PersistentSubsectionGradeOverride.DoesNotExist:
            override = None
            history = []

        results = SubsectionGradeResponseSerializer({
            'original_grade': original_grade,
            'override': override,
            'history': history,
            'subsection_id': original_grade.usage_key,
            'user_id': original_grade.user_id,
            'course_id': original_grade.course_id,
        })

        return Response(results.data)
