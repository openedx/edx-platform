""" API Views for Course Optimizer. """
import edx_api_doc_tools as apidocs
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from user_tasks.models import UserTaskStatus

from cms.djangoapps.contentstore.core.course_optimizer_provider import get_link_check_data, sort_course_sections
from cms.djangoapps.contentstore.rest_api.v0.serializers.course_optimizer import LinkCheckSerializer
from cms.djangoapps.contentstore.tasks import check_broken_links
from common.djangoapps.student.auth import has_course_author_access, has_studio_read_access
from common.djangoapps.util.json_request import JsonResponse
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes


@view_auth_classes(is_authenticated=True)
class LinkCheckView(DeveloperErrorViewMixin, APIView):
    """
    View for queueing a celery task to scan a course for broken links.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: "Celery task queued.",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def post(self, request: Request, course_id: str):
        """
        Queue celery task to scan a course for broken links.

        **Example Request**
            POST /api/contentstore/v0/link_check/{course_id}

        **Response Values**
        ```json
        {
            "LinkCheckStatus": "Pending"
        }
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        check_broken_links.delay(request.user.id, course_id, request.LANGUAGE_CODE)
        return JsonResponse({'LinkCheckStatus': UserTaskStatus.PENDING})


@view_auth_classes()
class LinkCheckStatusView(DeveloperErrorViewMixin, APIView):
    """
    View for checking the status of the celery task and returning the results.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: "OK",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    def get(self, request: Request, course_id: str):
        """
        GET handler to return the status of the link_check task from UserTaskStatus.
        If no task has been started for the course, return 'Uninitiated'.
        If link_check task was successful, an output result is also returned.

        For reference, the following status are in UserTaskStatus:
            'Pending', 'In Progress' (sent to frontend as 'In-Progress'),
            'Succeeded', 'Failed', 'Canceled', 'Retrying'
        This function adds a status for when status from UserTaskStatus is None:
            'Uninitiated'

        **Example Request**
            GET /api/contentstore/v0/link_check_status/{course_id}

        **Example Response**
        ```json
        {
            "LinkCheckStatus": "Succeeded",
            "LinkCheckCreatedAt": "2025-02-05T14:32:01.294587Z",
            "LinkCheckOutput": {
                sections: [
                    {
                        id: <string>,
                        displayName: <string>,
                        subsections: [
                            {
                                id: <string>,
                                displayName: <string>,
                                units: [
                                    {
                                        id: <string>,
                                        displayName: <string>,
                                        blocks: [
                                            {
                                                id: <string>,
                                                url: <string>,
                                                brokenLinks: [
                                                    <string>,
                                                    <string>,
                                                    <string>,
                                                    ...,
                                                ],
                                                lockedLinks: [
                                                    <string>,
                                                    <string>,
                                                    <string>,
                                                    ...,
                                                ],
                                            },
                                            { <another block> },
                                        ],
                                    },
                                    { <another unit> },
                                ],
                            },
                            { <another subsection },
                        ],
                    },
                    { <another section> },
                ],
            },
        }
        """
        course_key = CourseKey.from_string(course_id)
        if not has_course_author_access(request.user, course_key):
            print('missing course author access')
            self.permission_denied(request)

        data = get_link_check_data(request, course_id)
        data = sort_course_sections(course_key, data)

        serializer = LinkCheckSerializer(data)
        return Response(serializer.data)
