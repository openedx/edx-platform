"""
Public rest API endpoints for the CMS API video assets.
"""
import edx_api_doc_tools as apidocs
import logging
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import (MultiPartParser, FormParser)
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes, verify_course_exists
from openedx.core.lib.api.parsers import TypedFileUploadParser
from common.djangoapps.student.auth import has_studio_read_access
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required
from ....utils import get_course_videos_context

from cms.djangoapps.contentstore.video_storage_handlers import (
    handle_videos,
    get_video_encodings_download,
    handle_video_images,
    enabled_video_features,
    get_video_usage_path
)
from cms.djangoapps.contentstore.rest_api.v1.serializers import (
    CourseVideosSerializer,
    VideoUploadSerializer,
    VideoImageSerializer,
    VideoUsageSerializer,
)
import cms.djangoapps.contentstore.toggles as contentstore_toggles
from .utils import validate_request_with_serializer


log = logging.getLogger(__name__)
toggles = contentstore_toggles


@view_auth_classes(is_authenticated=True)
class CourseVideosView(DeveloperErrorViewMixin, APIView):
    """
    View for course videos.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseVideosSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested course does not exist",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing course videos.
        **Example Request**
            GET /api/contentstore/v1/videos/{course_id}/{edx_video_id}
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response contains a single dict that contains keys that
        are the course's videos.
        **Example Response**
        ```json
        {
            image_upload_url: '/video_images/course_id',
            video_handler_url: '/videos/course_id',
            encodings_download_url: '/video_encodings_download/course_id',
            default_video_image_url: '/static/studio/images/video-images/default_video_image.png',
            previous_uploads: [
                {
                    edx_video_id: 'mOckID1',
                    clientVideoId: 'mOckID1.mp4',
                    created: '',
                    courseVideoImageUrl: '/video',
                    transcripts: [],
                    status: 'Imported',
                    file_size: 123,
                    download_link: 'http:/download_video.com'
                },
                {
                    edx_video_id: 'mOckID5',
                    clientVideoId: 'mOckID5.mp4',
                    created: '',
                    courseVideoImageUrl: 'http:/video',
                    transcripts: ['en'],
                    status: 'Failed',
                    file_size: 0,
                    download_link: ''
                },
                {
                    edx_video_id: 'mOckID3',
                    clientVideoId: 'mOckID3.mp4',
                    created: '',
                    courseVideoImageUrl: null,
                    transcripts: ['en'],
                    status: 'Ready',
                    file_size: 123,
                    download_link: 'http:/download_video.com'
                },
            ],
            concurrent_upload_limit: 4,
            video_supported_file_formats: ['.mp4', '.mov'],
            video_upload_max_file_size: '5',
            video_image_settings: {
                video_image_upload_enabled: false,
                max_size: 2097152,
                min_size: 2048,
                max_width: 1280,
                max_height: 720,
                supported_file_formats: {
                    '.bmp': 'image/bmp',
                    '.bmp2': 'image/x-ms-bmp',
                    '.gif': 'image/gif',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                },
            },
            is_video_transcript_enabled: false,
            active_transcript_preferences: null,
            transcript_credentials: {},
            transcript_available_languages: [{ language_code: 'ab', language_text: 'Abkhazian' }],
            video_transcript_settings: {
                transcript_download_handler_url: '/transcript_download/',
                transcript_upload_handler_url: '/transcript_upload/',
                transcript_delete_handler_url: '/transcript_delete/course_id',
                trancript_download_file_format: 'srt',
            },
            pagination_context: {},
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        course_videos_context = get_course_videos_context(
            None,
            None,
            course_key,
        )
        serializer = CourseVideosSerializer(course_videos_context)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class VideoUsageView(DeveloperErrorViewMixin, APIView):
    """
    View for course video usage locations.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter("edx_video_id", apidocs.ParameterLocation.PATH, description="edX Video ID"),
        ],
        responses={
            200: VideoUsageSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested course does not exist",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str, edx_video_id: str):
        """
        Get an object containing course videos.
        **Example Request**
            GET /api/contentstore/v1/videos/{course_id}/{edx_video_id}
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response contains a single dict that contains keys that
        are the course's videos.
        **Example Response**
        ```json
        {
            "usage_locations": ["subsection - unit/xblock"],
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        usage_locations = get_video_usage_path(request, course_key, edx_video_id)
        serializer = VideoUsageSerializer(usage_locations)
        return Response(serializer.data)


@view_auth_classes()
class VideosUploadsView(DeveloperErrorViewMixin, RetrieveAPIView, DestroyAPIView):
    """
    public rest API endpoints for the CMS API video assets.
    course_key: required argument, needed to authorize course authors and identify the video.
    video_id: required argument, needed to identify the video.
    """
    serializer_class = VideoUploadSerializer

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @course_author_access_required
    def retrieve(self, request, course_key, edx_video_id=None):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id(), edx_video_id)

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, edx_video_id):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id(), edx_video_id)


@view_auth_classes()
class VideosCreateUploadView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoints for the CMS API video assets.
    course_key: required argument, needed to authorize course authors and identify the video.
    """
    serializer_class = VideoUploadSerializer

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    @validate_request_with_serializer
    def create(self, request, course_key):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id())


@view_auth_classes()
class VideoImagesView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoint for uploading a video image.
    course_key: required argument, needed to authorize course authors and identify the video.
    video_id: required argument, needed to identify the video.
    """
    serializer_class = VideoImageSerializer
    parser_classes = (MultiPartParser, FormParser, TypedFileUploadParser)

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    @validate_request_with_serializer
    def create(self, request, course_key, edx_video_id=None):  # pylint: disable=arguments-differ
        return handle_video_images(request, course_key.html_id(), edx_video_id)


@view_auth_classes()
class VideoEncodingsDownloadView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    public rest API endpoint providing a CSV report containing the encoded video URLs for video uploads.
    course_key: required argument, needed to authorize course authors and identify relevant videos.
    """

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    def retrieve(self, request, course_key):  # pylint: disable=arguments-differ
        return get_video_encodings_download(request, course_key.html_id())


@view_auth_classes()
class VideoFeaturesView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    public rest API endpoint providing a list of enabled video features.
    """

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def retrieve(self, request):  # pylint: disable=arguments-differ
        return enabled_video_features(request)
