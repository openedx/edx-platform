"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.core.cache import cache
from django.http import HttpResponse

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment, User

from .serializers import BlockOutline, video_summary
from public_api import get_mobile_course


class VideoSummaryList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = get_mobile_course(course_id)

        transcripts_cache_key = "VideoSummaryList.transcripts.langs.{}".format(course_id)
        original_transcripts_langs_cache = cache.get(transcripts_cache_key, {})
        local_cache = {'transcripts_langs': dict(original_transcripts_langs_cache)}

        video_outline = list(
            BlockOutline(
                course_id,
                course,
                {"video": partial(video_summary, course)},
                request,
                local_cache,
            )
        )
        # If we added any entries, renew the cache...
        if local_cache['transcripts_langs'] != original_transcripts_langs_cache:
            cache.set(transcripts_cache_key, local_cache['transcripts_langs'])

        return Response(video_outline)


class VideoTranscripts(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_key = CourseKey.from_string(kwargs['course_id'])
        block_id = kwargs['block_id']
        lang = kwargs['lang']

        usage_key = BlockUsageLocator(
            course_key, block_type="video", block_id=block_id
        )
        video_descriptor = modulestore().get_item(usage_key)
        content, filename, mimetype = video_descriptor.get_transcript(lang=lang)

        response = HttpResponse(content, content_type=mimetype)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        return response


