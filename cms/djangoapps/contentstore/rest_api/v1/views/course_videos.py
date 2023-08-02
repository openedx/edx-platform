""" API Views for course videos """
from typing import Optional

import edx_api_doc_tools as apidocs
from edxval.api import remove_video_for_course, VideoSortField, SortDirection
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.auth import has_studio_read_access
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes
from ..serializers.course_videos import CourseVideosSerializer
from ....views.videos import get_index_videos, get_and_validate_course, get_video


@view_auth_classes(is_authenticated=True)
class CourseVideosView(DeveloperErrorViewMixin, APIView):
    """
    View for course videos.
    """

    def get_course_and_check_access(self, course_id, request):
        course = get_and_validate_course(course_id, request.user)
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        if not course:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message=f"Course with id {course_id} does not exist",
                error_code='course_does_not_exist'
            )
        return course

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter("edx_video_id", apidocs.ParameterLocation.PATH, description="Video ID"),
        ],
        responses={
            200: CourseVideosSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course or video does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str, edx_video_id: Optional[str] = None):
        """
        Get a list of all videos for the course, or a single video from the course.

        **Example Request**

            GET /api/contentstore/v1/videos/{course_id}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a list of dicts that contains details
        about the videos in the course.

        **Example Response**

        ```json
        [
            {
                "client_video_id": "Some Video",
                "course_video_image_url": null,
                "created": "2022-09-07T04:56:58.626583Z",
                "duration": 11.4,
                "edx_video_id": "5ef286e8-8e15-4b9c-a02c-f41cd38cb0b6",
                "status": "Unknown"
            },
            ...
        ]
        ```

        **Example Request**

            GET /api/contentstore/v1/videos/{course_id}/{edx_video_id}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains details about
        the video.

        **Example Response**

        ```json
        [
            {
                "client_video_id": "Some Video",
                "course_video_image_url": null,
                "created": "2022-09-07T04:56:58.626583Z",
                "duration": 11.4,
                "edx_video_id": "5ef286e8-8e15-4b9c-a02c-f41cd38cb0b6",
                "status": "Unknown"
            },
            ...
        ]
        ```
        """
        course = self.get_course_and_check_access(course_id, request)

        pagination_conf = {
            'page_number': int(request.query_params.get('page', 1)),
            'videos_per_page': int(request.query_params.get('per_page', 10)),
        }

        try:
            sort_field = VideoSortField(request.query_params.get('sort_by', 'edx_video_id'))
            sort_direction = SortDirection(request.query_params.get('sort_dir', 'desc'))
        except ValueError:
            raise self.api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                developer_message="Unsupported sort field or direction",
                error_code='invalid_sort',
            )

        if edx_video_id:
            video = get_video(course, edx_video_id)
            if video is None:
                raise self.api_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    developer_message=f"Video with id {edx_video_id} does not exist",
                    error_code='video_does_not_exist'
                )
            serializer = CourseVideosSerializer(video)
            return Response(serializer.data)
        else:
            course_videos, pagination = get_index_videos(
                course,
                pagination_conf=pagination_conf,
                sort_field=sort_field,
                sort_direction=sort_direction,
            )
            serializer = CourseVideosSerializer(course_videos, many=True)
            return Response({
                "pagination": pagination,
                "videos": serializer.data,
            })

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter("edx_video_id", apidocs.ParameterLocation.PATH, description="Video ID"),
        ],
        responses={
            204: "In case of success, a 204 is returned with no content.",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course or video does not exist.",
        },
    )
    @verify_course_exists()
    def delete(self, request: Request, course_id: str, edx_video_id: str):
        """
        Delete a video from a course.

        **Example Request**

            DELETE /api/contentstore/v1/videos/{course_id}/{edx_video_id}

        **Response Values**

        If the request is successful, an HTTP 204 response is returned.
        """
        self.get_course_and_check_access(course_id, request)
        remove_video_for_course(course_id, edx_video_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
