"""
Define some view level utility functions here that multiple view modules will share
"""
from contextlib import contextmanager
from functools import wraps

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type

from django.contrib.auth import get_user_model
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from student.models import CourseEnrollment
from util.query import use_read_replica_if_available

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


class CourseEnrollmentPagination(CursorPagination):
    """
    Paginates over CourseEnrollment objects.
    """
    ordering = 'id'
    page_size = 50
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        """
        Get the page size based on the defined page size parameter if defined.
        """
        try:
            page_size_string = request.query_params[self.page_size_query_param]
            return int(page_size_string)
        except (KeyError, ValueError):
            pass

        return self.page_size


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

    def _paginate_users(self, course_key, course_enrollment_filter=None, related_models=None):
        """
        Args:
            course_key (CourseLocator): The course to retrieve grades for.
            course_enrollment_filter: Optional dictionary of keyword arguments to pass
            to `CourseEnrollment.filter()`.
            related_models: Optional list of related models to join to the CourseEnrollment table.

        Returns:
            A list of users, pulled from a paginated queryset of enrollments, who are enrolled in the given course.
        """
        filter_kwargs = {
            'course_id': course_key,
            'is_active': True,
        }
        filter_kwargs.update(course_enrollment_filter or {})
        enrollments_in_course = use_read_replica_if_available(
            CourseEnrollment.objects.filter(**filter_kwargs)
        )
        if related_models:
            enrollments_in_course = enrollments_in_course.select_related(*related_models)

        paged_enrollments = self.paginate_queryset(enrollments_in_course)
        return [enrollment.user for enrollment in paged_enrollments]

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
