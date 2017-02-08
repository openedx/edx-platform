"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.http import Http404, HttpResponse
from mobile_api.models import MobileApiConfig

from rest_framework import generics
from rest_framework.response import Response
from opaque_keys.edx.locator import BlockUsageLocator

from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore

from ..decorators import mobile_course_access, mobile_view
from .serializers import BlockOutline, video_summary


@mobile_view()
class VideoSummaryList(generics.ListAPIView):
    """
    **Use Case**

        Get a list of all videos in the specified course. You can use the
        video_url value to access the video file.

    **Example Request**

        GET /api/mobile/v0.5/video_outlines/courses/{organization}/{course_number}/{course_run}

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with an array of videos in the course. The array
        includes the following information for each video.

            * named_path: An array that consists of the display names of the
              courseware objects in the path to the video.
            * path: An array that specifies the complete path to the video in
              the courseware hierarchy. The array contains the following
              values.

                * category: The type of division in the course outline.
                  Possible values are "chapter", "sequential", and "vertical".
                * name: The display name for the object.
                * id: The The unique identifier for the video.

            * section_url: The URL to the first page of the section that
              contains the video in the Learning Management System.
            * summary: An array of data about the video that includes the
              following values.

                * category: The type of component. This value will always be "video".
                * duration: The length of the video, if available.
                * id: The unique identifier for the video.
                * language: The language code for the video.
                * name:  The display name of the video.
                * size: The size of the video file.
                * transcripts: An array of language codes and URLs to available
                  video transcripts. Use the URL value to access a transcript
                  for the video.
                * video_thumbnail_url: The URL to the thumbnail image for the
                  video, if available.
                * video_url: The URL to the video file. Use this value to access
                  the video.

            * unit_url: The URL to the unit that contains the video in the Learning
              Management System.
    """

    @mobile_course_access(depth=None)
    def list(self, request, course, *args, **kwargs):
        video_profiles = MobileApiConfig.get_video_profiles()
        video_outline = list(
            BlockOutline(
                course.id,
                course,
                {"video": partial(video_summary, video_profiles)},
                request,
                video_profiles,
            )
        )
        return Response(video_outline)


@mobile_view()
class VideoTranscripts(generics.RetrieveAPIView):
    """
    **Use Case**

        Get a transcript for a specified video and language.

    **Example request**

        GET /api/mobile/v0.5/video_outlines/transcripts/{organization}/{course_number}/{course_run}/{video ID}/{language code}

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with an .srt file that you can download.

    """

    @mobile_course_access()
    def get(self, request, course, *args, **kwargs):
        block_id = kwargs['block_id']
        lang = kwargs['lang']

        usage_key = BlockUsageLocator(
            course.id, block_type="video", block_id=block_id
        )
        try:
            video_descriptor = modulestore().get_item(usage_key)
            transcripts = video_descriptor.get_transcripts_info()
            content, filename, mimetype = video_descriptor.get_transcript(transcripts, lang=lang)
        except (NotFoundError, ValueError, KeyError):
            raise Http404(u"Transcript not found for {}, lang: {}".format(block_id, lang))

        response = HttpResponse(content, content_type=mimetype)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename.encode('utf-8'))

        return response
