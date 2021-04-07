"""
Define some view level utility functions here that multiple view modules will share
"""


from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.query import use_read_replica_if_available
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.grade_utils import serialize_user_grade
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

USER_MODEL = get_user_model()


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

    def get_paginated_response(self, data, status_code=200, **kwargs):  # pylint: disable=arguments-differ
        """
        Return a response given serialized page data, optional status_code (defaults to 200),
        and kwargs. Each key-value pair of kwargs is added to the response data.
        """
        resp = super().get_paginated_response(data)

        for (key, value) in kwargs.items():
            resp.data[key] = value

        resp.status_code = status_code
        return resp


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
            raise self.api_error(  # lint-amnesty, pylint: disable=raise-missing-from
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user matching the requested username does not exist.',
                error_code='user_does_not_exist'
            )
        except CourseEnrollment.DoesNotExist:
            raise self.api_error(  # lint-amnesty, pylint: disable=raise-missing-from
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
        return Response([serialize_user_grade(grade_user, course_key, course_grade)])

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser).
        """
        super().perform_authentication(request)
        if request.user.is_anonymous:
            raise AuthenticationFailed
