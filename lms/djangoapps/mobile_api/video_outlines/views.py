"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.core.cache import cache
from django.http import Http404, HttpResponse

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from courseware.access import has_access
from student.models import CourseEnrollment, User
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore

from .serializers import BlockOutline, video_summary


class VideoSummaryList(generics.ListAPIView):
    """A list of all Videos in this Course that the user has access to."""
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
    """Read-only view for a single transcript (SRT) file for a particular language.

    Returns an `HttpResponse` with an SRT file download for the body.
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
            raise Http404("Transcript not found for {}, lang: {}".format(block_id, lang))

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
