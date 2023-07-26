"""
Public rest API endpoints for the Studio Content API video assets.
"""
import logging
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view, JsonResponse

from ....api import course_author_access_required

from cms.djangoapps.contentstore.transcript_storage_handlers import (
    upload_transcript,
    delete_video_transcript,
    handle_transcript_credentials,
    handle_transcript_download,
)
import cms.djangoapps.contentstore.toggles as contentstore_toggles

log = logging.getLogger(__name__)
toggles = contentstore_toggles

@view_auth_classes()
class TranscriptView(DeveloperErrorViewMixin, CreateAPIView, RetrieveAPIView, DestroyAPIView):
    """
    public rest API endpoints for the Studio Content API video transcripts.
    course_key: required argument, needed to authorize course authors and identify the video.
    edx_video_id: optional argument, needed to identify the video.
    language_code: optional argument.
    """

    def dispatch(self, request, *args, **kwargs):
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key_string):  # pylint: disable=arguments-differ
        return upload_transcript(request)

    @course_author_access_required
    def retrieve(self, request, course_key_string):  # pylint: disable=arguments-differ
        return handle_transcript_download(request)

    @course_author_access_required
    def destroy(self, request, course_key_string, edx_video_id, language_code):  # pylint: disable=arguments-differ
        delete_video_transcript(edx_video_id, language_code)
        return JsonResponse(status=200)


@view_auth_classes()
class TranscriptCredentialsView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoints for the Studio Content API video transcript credentials.
    Allows you to update transcript credentials.
    course_key: required argument, needed to authorize course authors and identify the video.
    """
    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key_string):  # pylint: disable=arguments-differ
        return handle_transcript_credentials(request, course_key_string)
