""" API implementation for course-oriented interactions. """

import logging

from django.conf import settings
from django.http import Http404
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

from course_structure_api.v0 import serializers
from courseware import courses
from courseware.access import has_access
from openedx.core.djangoapps.content.course_structures import models, tasks
from openedx.core.lib.api.permissions import IsAuthenticatedOrDebug
from openedx.core.lib.api.serializers import PaginationSerializer
from student.roles import CourseInstructorRole, CourseStaffRole


log = logging.getLogger(__name__)


class CourseViewMixin(object):
    """
    Mixin for views dealing with course content. Also handles authorization and authentication.
    """
    lookup_field = 'course_id'
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticatedOrDebug,)

    def get_course_or_404(self):
        """
        Retrieves the specified course, or raises an Http404 error if it does not exist.
        Also checks to ensure the user has permissions to view the course
        """
        try:
            course_id = self.kwargs.get('course_id')
            course_key = CourseKey.from_string(course_id)
            course = courses.get_course(course_key)

            self.check_course_permissions(self.request.user, course)

            return course
        except ValueError:
            raise Http404

    def user_can_access_course(self, user, course):
        """
        Determines if the user is staff or an instructor for the course.
        Always returns True if DEBUG mode is enabled.
        """
        return (settings.DEBUG
                or has_access(user, CourseStaffRole.ROLE, course)
                or has_access(user, CourseInstructorRole.ROLE, course))

    def check_course_permissions(self, user, course):
        """
        Checks if the request user can access the course.
        Raises PermissionDenied if the user does not have course access.
        """
        if not self.user_can_access_course(user, course):
            raise PermissionDenied

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

        CourseList returns paginated list of courses in the edX Platform. The list can be filtered by course_id.

    **Example Request**

          GET /api/course_structure/v0/courses/
          GET /api/course_structure/v0/courses/?course_id={course_id1},{course_id2}

    **Response Values**

        * id: The unique identifier for the course.

        * name: The name of the course.

        * category: The type of content. In this case, the value is always "course".

        * org: The organization specified for the course.

        * course: The course number.

        * org: The run for the course.

        * uri: The URI to use to get details of the course.

        * image_url: The URI for the course's main image.

        * start: Course start date

        * end: Course end date
    """
    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = serializers.CourseSerializer

    def get_queryset(self):
        course_ids = self.request.QUERY_PARAMS.get('course_id', None)

        results = []
        if course_ids:
            course_ids = course_ids.split(',')
            for course_id in course_ids:
                course_key = CourseKey.from_string(course_id)
                course_descriptor = courses.get_course(course_key)
                results.append(course_descriptor)
        else:
            results = modulestore().get_courses()

        # Ensure only course descriptors are returned.
        results = (course for course in results if course.scope_ids.block_type == 'course')

        # Ensure only courses accessible by the user are returned.
        results = (course for course in results if self.user_can_access_course(self.request.user, course))

        # Sort the results in a predictable manner.
        return sorted(results, key=lambda course: unicode(course.id))


class CourseDetail(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        CourseDetail returns details for a course.

    **Example requests**:

        GET /api/course_structure/v0/courses/{course_id}/

    **Response Values**

        * category: The type of content.

        * name: The name of the course.

        * uri: The URI to use to get details of the course.

        * course: The course number.

        * due:  The due date. For courses, the value is always null.

        * org: The organization specified for the course.

        * id: The unique identifier for the course.
    """

    serializer_class = serializers.CourseSerializer

    def get_object(self, queryset=None):
        return self.get_course_or_404()


class CourseStructure(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Retrieves course structure.

    **Example requests**:

        GET /api/course_structure/v0/course_structures/{course_id}/

    **Response Values**

        * root: ID of the root node of the structure

        * blocks: Dictionary mapping IDs to block nodes.
    """
    serializer_class = serializers.CourseStructureSerializer
    course = None

    def retrieve(self, request, *args, **kwargs):
        try:
            return super(CourseStructure, self).retrieve(request, *args, **kwargs)
        except models.CourseStructure.DoesNotExist:
            # If we don't have data stored, generate it and return a 503.
            tasks.update_course_structure.delay(unicode(self.course.id))
            return Response(status=503, headers={'Retry-After': '120'})

    def get_object(self, queryset=None):
        # Make sure the course exists and the user has permissions to view it.
        self.course = self.get_course_or_404()
        course_structure = models.CourseStructure.objects.get(course_id=self.course.id)
        return course_structure.structure


class CourseGradingPolicy(CourseViewMixin, ListAPIView):
    """
    **Use Case**

        Retrieves course grading policy.

    **Example requests**:

        GET /api/course_structure/v0/grading_policies/{course_id}/

    **Response Values**

        * assignment_type: The type of the assignment (e.g. Exam, Homework). Note: These values are course-dependent.
          Do not make any assumptions based on assignment type.

        * count: Number of assignments of the type.

        * dropped: Number of assignments of the type that are dropped.

        * weight: Effect of the assignment type on grading.
    """

    serializer_class = serializers.GradingPolicySerializer
    allow_empty = False

    def get_queryset(self):
        course = self.get_course_or_404()

        # Return the raw data. The serializer will handle the field mappings.
        return course.raw_grader
