""" API implementation for course-oriented interactions. """

import logging

from django.conf import settings
from django.http import Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

from course_structure_api.v0 import serializers
from courseware import courses
from courseware.access import has_access
from openedx.core.djangoapps.content.course_structures.api.v0 import api, errors
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


class CourseList(CourseViewMixin, ListAPIView):
    """
    **Use Case**

        Get a paginated list of courses in the edX Platform.

        The list can be filtered by course_id.

        Each page in the list can contain up to 10 courses.

    **Example Requests**

          GET /api/course_structure/v0/courses/

          GET /api/course_structure/v0/courses/?course_id={course_id1},{course_id2}

    **Response Values**

        * count: The number of courses in the edX platform.

        * next: The URI to the next page of courses.

        * previous: The URI to the previous page of courses.

        * num_pages: The number of pages listing courses.

        * results:  A list of courses returned. Each collection in the list
          contains these fields.

            * id: The unique identifier for the course.

            * name: The name of the course.

            * category: The type of content. In this case, the value is always
              "course".

            * org: The organization specified for the course.

            * run: The run of the course.

            * course: The course number.

            * uri: The URI to use to get details of the course.

            * image_url: The URI for the course's main image.

            * start: The course start date.

            * end: The course end date. If course end date is not specified, the
              value is null.
    """
    serializer_class = serializers.CourseSummarySerializer

    def get_queryset(self):
        course_ids = self.request.query_params.get('course_id', None)

        results = []
        if course_ids:
            course_ids = course_ids.split(',')
            for course_id in course_ids:
                course_key = CourseKey.from_string(course_id)
                course_descriptor = courses.get_course(course_key)
                results.append(course_descriptor)
        else:
            results = modulestore().get_course_summaries()

        # Ensure only courses accessible by the user are returned.
        results = (course for course in results if self.user_can_access_course(self.request.user, course.id))

        # Sort the results in a predictable manner.
        return sorted(results, key=lambda course: unicode(course.id))


class CourseDetail(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Get details for a specific course.

    **Example Request**:

        GET /api/course_structure/v0/courses/{course_id}/

    **Response Values**

        * id: The unique identifier for the course.

        * name: The name of the course.

        * category: The type of content.

        * org: The organization that is offering the course.

        * run: The run of the course.

        * course: The course number.

        * uri: The URI to use to get details about the course.

        * image_url: The URI for the course's main image.

        * start: The course start date.

        * end: The course end date. If course end date is not specified, the
          value is null.
    """
    serializer_class = serializers.CourseSerializer

    def get_object(self, queryset=None):
        return self.get_course_or_404()


class CourseStructure(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Get the course structure. This endpoint returns all blocks in the
        course.

    **Example requests**:

        GET /api/course_structure/v0/course_structures/{course_id}/

    **Response Values**

        * root: The ID of the root node of the course structure.

        * blocks: A dictionary that maps block IDs to a collection of
          information about each block. Each block contains the following
          fields.

          * id: The ID of the block.

          * type: The type of block. Possible values include sequential,
            vertical, html, problem, video, and discussion. The type can also be
            the name of a custom type of block used for the course.

          * display_name: The display name configured for the block.

          * graded: Whether or not the sequential or problem is graded. The
            value is true or false.

          * format: The assignment type.

          * children: If the block has child blocks, a list of IDs of the child
            blocks in the order they appear in the course.
    """

    @CourseViewMixin.course_check
    def get(self, request, **kwargs):
        try:
            return Response(api.course_structure(self.course_key))
        except errors.CourseStructureNotAvailableError:
            # If we don't have data stored, we will try to regenerate it, so
            # return a 503 and as them to retry in 2 minutes.
            return Response(status=503, headers={'Retry-After': '120'})


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
