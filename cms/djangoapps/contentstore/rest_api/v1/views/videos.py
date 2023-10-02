"""
Public rest API endpoints for the CMS API video assets.
"""
import logging
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from rest_framework.parsers import (MultiPartParser, FormParser)
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.lib.api.parsers import TypedFileUploadParser
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.video_storage_handlers import (
    handle_videos,
    get_video_encodings_download,
    handle_video_images,
    enabled_video_features
)
from cms.djangoapps.contentstore.rest_api.v1.serializers import VideoUploadSerializer, VideoImageSerializer
import cms.djangoapps.contentstore.toggles as contentstore_toggles
from .utils import validate_request_with_serializer


log = logging.getLogger(__name__)
toggles = contentstore_toggles


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
