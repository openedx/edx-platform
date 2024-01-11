"""API Views for course index"""

import edx_api_doc_tools as apidocs
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.rest_api.v1.serializers import CourseIndexSerializer
from cms.djangoapps.contentstore.utils import get_course_index_context
from common.djangoapps.student.auth import has_studio_read_access
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes


@view_auth_classes(is_authenticated=True)
class CourseIndexView(DeveloperErrorViewMixin, APIView):
    """View for Course Index"""

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter(
                "show",
                apidocs.ParameterLocation.QUERY,
                description="Query param to set initial state which fully expanded to see the item",
            )],
        responses={
            200: CourseIndexSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing course index for outline.

        **Example Request**

            GET /api/contentstore/v1/course_index/{course_id}?show=block-v1:edx+101+y+type@course+block@course

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's outline.

        **Example Response**

        ```json
        {
            "course_release_date": "Set Date",
            "course_structure": {},
            "deprecated_blocks_info": {
                "deprecated_enabled_block_types": [],
                "blocks": [],
                "advance_settings_url": "/settings/advanced/course-v1:edx+101+y76"
            },
            "discussions_incontext_feedback_url": "",
            "discussions_incontext_learnmore_url": "",
            "initial_state": {
                "expanded_locators": [
                "block-v1:edx+101+y76+type@chapter+block@03de0adc9d1c4cc097062d80eb04abf6",
                "block-v1:edx+101+y76+type@sequential+block@8a85e287e30a47e98d8c1f37f74a6a9d"
                ],
                "locator_to_show": "block-v1:edx+101+y76+type@chapter+block@03de0adc9d1c4cc097062d80eb04abf6"
            },
            "initial_user_clipboard": {
                "content": null,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": ""
            },
            "language_code": "en",
            "lms_link": "//localhost:18000/courses/course-v1:edx+101+y76/jump_to/block-v1:edx+101+y76",
            "mfe_proctored_exam_settings_url": "",
            "notification_dismiss_url": "/course_notifications/course-v1:edx+101+y76/2",
            "proctoring_errors": [],
            "reindex_link": "/course/course-v1:edx+101+y76/search_reindex",
            "rerun_notification_id": 2
        }
        ```
        """

        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)
        course_index_context = get_course_index_context(request, course_key)
        course_index_context.update({
            "discussions_incontext_learnmore_url": settings.DISCUSSIONS_INCONTEXT_LEARNMORE_URL,
            "discussions_incontext_feedback_url": settings.DISCUSSIONS_INCONTEXT_FEEDBACK_URL,
        })

        serializer = CourseIndexSerializer(course_index_context)
        return Response(serializer.data)
