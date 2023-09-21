"""
Public rest API endpoints for the CMS API video assets.
"""
import logging
from rest_framework import serializers
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponseBadRequest

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.transcript_storage_handlers import (
    upload_transcript,
    delete_video_transcript_or_404,
    handle_transcript_download,
)
import cms.djangoapps.contentstore.toggles as contentstore_toggles
from cms.djangoapps.contentstore.rest_api.v1.serializers import TranscriptSerializer
from rest_framework.parsers import (MultiPartParser, FormParser)
from openedx.core.lib.api.parsers import TypedFileUploadParser

log = logging.getLogger(__name__)
toggles = contentstore_toggles


@view_auth_classes()
class TranscriptView(DeveloperErrorViewMixin, CreateAPIView, RetrieveAPIView, DestroyAPIView):
    """
    public rest API endpoints for the CMS API video transcripts.
    course_key: required argument, needed to authorize course authors and identify the video.
    edx_video_id: optional query parameter, needed to identify the transcript.
    language_code: optional query parameter, needed to identify the transcript.
    """
    serializer_class=TranscriptSerializer
    parser_classes = (MultiPartParser, FormParser, TypedFileUploadParser)

    def dispatch(self, request, *args, **kwargs):
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key_string):  # pylint: disable=arguments-differ
        callback = lambda: upload_transcript(request)
        return _run_if_valid(request, context=self, callback=callback)

    @course_author_access_required
    def retrieve(self, request, course_key_string):  # pylint: disable=arguments-differ
        """
        Get a video transcript. edx_video_id and language_code query parameters are required.
        """
        return handle_transcript_download(request)

    @course_author_access_required
    def destroy(self, request, course_key_string):  # pylint: disable=arguments-differ
        """
        Delete a video transcript. edx_video_id and language_code query parameters are required.
        """

        return delete_video_transcript_or_404(request)


def _validate(request, context=None):
    """ Validate request data using the serializer in the context."""
    serializer = context.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)


def _run_if_valid(request, context=None, callback=None):
    """
    First, run a validation using the serializer in the context on the request data.
    If this succeeds, run the callback, else, return a 400 response.
    """
    try:
        _validate(request, context)
        return callback()
    except serializers.ValidationError as e:
        return HttpResponseBadRequest(reason=e.detail)
