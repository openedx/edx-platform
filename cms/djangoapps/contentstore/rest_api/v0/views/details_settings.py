""" API Views for course details settings """

import edx_api_doc_tools as apidocs
from opaque_keys.edx.keys import CourseKey
from rest_framework.request import Request
from rest_framework.views import APIView
from xmodule.modulestore.django import modulestore

from cms.djangoapps.models.settings.encoder import CourseSettingsEncoder
from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
from common.djangoapps.util.json_request import JsonResponse, expect_json
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes
from openedx.core.djangoapps.models.course_details import CourseDetails

from ....views.course import update_course_details_settings


@view_auth_classes(is_authenticated=True)
@expect_json
class CourseDetailsSettingsView(DeveloperErrorViewMixin, APIView):
    """
    View for getting and setting the details settings for a course.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing all the details settings in a course.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)
        course_details = CourseDetails.fetch(course_key)
        return JsonResponse(
            course_details,
            # encoder serializes dates, old locations, and instances
            encoder=CourseSettingsEncoder
        )

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def patch(self, request: Request, course_id: str):
        """
        Update a course's details settings.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_studio_write_access(request.user, course_key):
            self.permission_denied(request)
        course_block = modulestore().get_course(course_key)
        return update_course_details_settings(course_key, course_block, request)
