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
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes, verify_course_exists
from openedx.core.lib.api.parsers import TypedFileUploadParser
from common.djangoapps.student.auth import has_studio_read_access
from common.djangoapps.util.json_request import expect_json_in_class_view
from xmodule.modulestore.django import modulestore

from ....api import course_author_access_required
from ....utils import get_course_videos_context


from cms.djangoapps.contentstore.video_storage_handlers import (
    handle_videos,
    get_video_encodings_download,
    handle_video_images,
    enabled_video_features,
    _get_index_videos,
    generate_video_download_link,
    get_video_usage_path
)
from cms.djangoapps.contentstore.rest_api.v1.serializers import (
  CourseVideosSerializer,
  VideoUploadSerializer,
  VideoImageSerializer,
  VideoDownloadSerializer,
  VideoUsageSerializer,
)
from cms.djangoapps.contentstore.video_storage_handlers import get_all_transcript_languages
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
            "allow_unicode_course_id": False,
            "course_creator_status": "granted",
            "number": "101",
            "display_name": "new edx course",
            "org": "edx",
            "run": "2023",
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)            

        transcript_languages = get_all_transcript_languages()
        default_video_image_url = staticfiles_storage.url(settings.VIDEO_IMAGE_DEFAULT_FILENAME)
        with modulestore().bulk_operations(course_key):
            course_block = modulestore().get_course(course_key)
            videos = _get_index_videos(course_block)
            course_videos_context = get_course_videos_context(course_block, transcript_languages, videos, default_video_image_url)
        del course_videos_context['context_course']
        serializer = CourseVideosSerializer(course_videos_context)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class VideoDownloadView(DeveloperErrorViewMixin, APIView):
    """
    View for course video download.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter("edx_video_id", apidocs.ParameterLocation.PATH, description="edX Video ID"),
        ],
        responses={
            200: VideoDownloadSerializer,
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
            "download_link": "http://test-download.com/id",
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)
        
        download_link = generate_video_download_link(request, course_key, edx_video_id)
        serializer = VideoDownloadSerializer(download_link)
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
        print('LOCATION!!!!! \n', usage_locations)
        serializer = VideoUsageSerializer(usage_locations)
        return Response(serializer.data)
    

@view_auth_classes()
class TranscriptCredentialsView(DeveloperErrorViewMixin, APIView):
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
    def post(self, request: Request, course_id: str):
        pass


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
