"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.http import Http404, HttpResponse

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from courseware.access import has_access
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore

from .serializers import BlockOutline, video_summary


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
              contains the video in the Learning Managent System.

            * path: An array containing category and name values specifying the
              complete path the the video in the courseware hierarcy. The
              following categories values are included: "chapter", "sequential",
              and "vertical". The name value is the display name for that object.

            * unit_url: The URL to the unit contains the video in the Learning
              Managent System.

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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = get_mobile_course(course_id, request.user)

        video_outline = list(
            BlockOutline(
                course_id,
                course,
                {"video": partial(video_summary, course)},
                request,
            )
        )
        return Response(video_outline)


class VideoTranscripts(generics.RetrieveAPIView):
    """
    **Use Case**

        Use to get a transcript for a specified video and language.

    **Example request**:

        GET /api/mobile/v0.5/video_outlines/transcripts/{organization}/{course_number}/{course_run}/{video ID}/{language code}
    
    **Response Values**

        An HttpResponse with an SRT file download.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_key = CourseKey.from_string(kwargs['course_id'])
        block_id = kwargs['block_id']
        lang = kwargs['lang']

        usage_key = BlockUsageLocator(
            course_key, block_type="video", block_id=block_id
        )
        try:
            video_descriptor = modulestore().get_item(usage_key)
            content, filename, mimetype = video_descriptor.get_transcript(lang=lang)
        except (NotFoundError, ValueError, KeyError):
            raise Http404(u"Transcript not found for {}, lang: {}".format(block_id, lang))

        response = HttpResponse(content, content_type=mimetype)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        return response


def get_mobile_course(course_id, user):
    """
    Return only a CourseDescriptor if the course is mobile-ready or if the
    requesting user is a staff member.
    """
    course = modulestore().get_course(course_id, depth=None)
    if course.mobile_available or has_access(user, 'staff', course):
        return course

    raise PermissionDenied(detail="Course not available on mobile.")
