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

from ..utils import mobile_view, mobile_course_access
from .serializers import BlockOutline, video_summary


@mobile_view()
class VideoSummaryList(generics.ListAPIView):
    """
    **Use Case**

        Get a list of all videos in the specified course. You can use the
        video_url value to access the video file.

    **Example request**:

        GET /api/mobile/v0.5/video_outlines/courses/{organization}/{course_number}/{course_run}

    **Response Values**

        An array of videos in the course. For each video:

            * section_url: The URL to the first page of the section that
              contains the video in the Learning Management System.

            * path: An array containing category, name, and id values specifying the
              complete path the the video in the courseware hierarchy. The
              following categories values are included: "chapter", "sequential",
              and "vertical". The name value is the display name for that object.

            * unit_url: The URL to the unit contains the video in the Learning
              Management System.

            * named_path: An array consisting of the display names of the
              courseware objects in the path to the video.

            * summary:  An array of data about the video that includes:

                * category:  The type of component, in this case always "video".

                * video_thumbnail_url: The URL to the thumbnail image for the
                  video, if available.

                * language: The language code for the video.

                * name:  The display name of the video.

                * video_url: The URL to the video file. Use this value to access
                  the video.

                * duration: The length of the video, if available.

                * transcripts: An array of language codes and URLs to available
                  video transcripts. Use the URL value to access a transcript
                  for the video.

                * id: The unique identifier for the video.

                * size: The size of the video file
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

        Use to get a transcript for a specified video and language.

    **Example request**:

        GET /api/mobile/v0.5/video_outlines/transcripts/{organization}/{course_number}/{course_run}/{video ID}/{language code}

    **Response Values**

        An HttpResponse with an SRT file download.

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
            content, filename, mimetype = video_descriptor.get_transcript(lang=lang)
        except (NotFoundError, ValueError, KeyError):
            raise Http404(u"Transcript not found for {}, lang: {}".format(block_id, lang))

        response = HttpResponse(content, content_type=mimetype)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename.encode('utf-8'))

        return response
