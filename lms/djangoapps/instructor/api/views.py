"""Views for Instructor Dashboard API v2."""
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from lms.djangoapps.instructor import permissions as instructor_permissions
from lms.djangoapps.instructor.api.serializers import ORASerializer
from lms.djangoapps.instructor.ora import get_open_response_assessment_list
from openedx.core.lib.courses import get_course_by_id

log = logging.getLogger(__name__)


class ORAAssessmentsView(GenericAPIView):
    """
    View to list all Open Response Assessments (ORAs) for a given course.

    * Requires token authentication.
    * Only instructors or staff for the course are able to access this view.
    """
    permission_classes = [permissions.IsAuthenticated, instructor_permissions.InstructorPermission]
    permission_name = instructor_permissions.VIEW_DASHBOARD
    serializer_class = ORASerializer

    def get_course(self):
        """
        Retrieve the course object based on the course_id URL parameter.

        Validates that the course exists and is not deprecated.
        Raises NotFound if the course does not exist.
        """
        course_id = self.kwargs.get("course_id")
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError as exc:
            log.error("Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
            raise NotFound("Course not found") from exc
        if course_key.deprecated:
            raise NotFound("Course not found")
        course = get_course_by_id(course_key, depth=None)
        return course

    def get(self, request, *args, **kwargs):
        """
        Return a list of all ORAs for the specified course.
        """
        course = self.get_course()

        items = get_open_response_assessment_list(course)

        page = self.paginate_queryset(items)
        if page is None:
            # if pagination is not applied, serialize all items
            # This is a DRF's recommended pattern
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
