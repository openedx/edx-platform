""" API implementation for course-oriented interactions.

TODO: delete me once grading policy is implemented in course_api.
"""

import logging

from django.conf import settings
from django.http import Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from opaque_keys.edx.keys import CourseKey

from courseware import courses
from courseware.access import has_access
from openedx.core.djangoapps.content.course_structures.api.v0 import api
from openedx.core.lib.exceptions import CourseNotFoundError
from student.roles import CourseInstructorRole, CourseStaffRole


log = logging.getLogger(__name__)


class CourseViewMixin(object):
    """
    Mixin for views dealing with course content. Also handles authorization and authentication.
    """
    lookup_field = 'course_id'
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_course_or_404(self):
        """
        Retrieves the specified course, or raises an Http404 error if it does not exist.
        Also checks to ensure the user has permissions to view the course
        """
        try:
            course_id = self.kwargs.get('course_id')
            course_key = CourseKey.from_string(course_id)
            course = courses.get_course(course_key)
            self.check_course_permissions(self.request.user, course_key)

            return course
        except ValueError:
            raise Http404

    @staticmethod
    def course_check(func):
        """Decorator responsible for catching errors finding and returning a 404 if the user does not have access
        to the API function.

        :param func: function to be wrapped
        :returns: the wrapped function
        """
        def func_wrapper(self, *args, **kwargs):
            """Wrapper function for this decorator.

            :param *args: the arguments passed into the function
            :param **kwargs: the keyword arguments passed into the function
            :returns: the result of the wrapped function
            """
            try:
                course_id = self.kwargs.get('course_id')
                self.course_key = CourseKey.from_string(course_id)
                self.check_course_permissions(self.request.user, self.course_key)
                return func(self, *args, **kwargs)
            except CourseNotFoundError:
                raise Http404

        return func_wrapper

    def user_can_access_course(self, user, course):
        """
        Determines if the user is staff or an instructor for the course.
        Always returns True if DEBUG mode is enabled.
        """
        return bool(
            settings.DEBUG
            or has_access(user, CourseStaffRole.ROLE, course)
            or has_access(user, CourseInstructorRole.ROLE, course)
        )

    def check_course_permissions(self, user, course):
        """
        Checks if the request user can access the course.
        Raises 404 if the user does not have course access.
        """
        if not self.user_can_access_course(user, course):
            raise Http404

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser), unless DEBUG mode is enabled.
        """
        super(CourseViewMixin, self).perform_authentication(request)
        if request.user.is_anonymous() and not settings.DEBUG:
            raise AuthenticationFailed


class CourseGradingPolicy(CourseViewMixin, ListAPIView):
    """
    **Use Case**

        Get the course grading policy.

    **Example requests**:

        GET /api/course_structure/v0/grading_policies/{course_id}/

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

    @CourseViewMixin.course_check
    def get(self, request, **kwargs):
        return Response(api.course_grading_policy(self.course_key))
