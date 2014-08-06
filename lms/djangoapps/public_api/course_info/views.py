"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from courseware.courses import get_course_about_section, course_image_url
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from student.models import CourseEnrollment, User

# section_key values are 'updates', 'handouts'

def get_course_info_module(request, course_id, section_key):
    course = modulestore().get_course(course_id)
    usage_key = course.id.make_usage_key('course_info', section_key)

    # Empty cache
    field_data_cache = FieldDataCache([], course.id, request.user)

    return get_module(
        request.user,
        request,
        usage_key,
        field_data_cache,
        course.id,
        wrap_xmodule_display=False,
        static_asset_path=course.static_asset_path
    )


class CourseUpdatesList(generics.ListAPIView):
    """Notes:

    1. This only works for new-style course updates and is not the older freeform
       format.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        course_updates_module = get_course_info_module(request, course_id, 'updates')
        return Response(reversed(course_updates_module.items))


class CourseHandoutsList(generics.ListAPIView):
    """Please just render this in an HTML view for now.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        course_handouts_module = get_course_info_module(request, course_id, 'handouts')
        return Response({'handouts_html': course_handouts_module.data})


class CourseAboutDetail(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_id = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        # There are other fields, but they don't seem to be in use.
        # see courses.py:get_course_about_section
        return Response(
            {
                "overview": get_course_about_section(course, "overview").strip(),
                "course-number": course.id.to_deprecated_string(),
                "status": "new" if course.is_newish else None,
                "title": get_course_about_section(course, 'title'),
                "course_image_url": course_image_url(course),
                "short_description": get_course_about_section(course, 'short_description'),
                "university": get_course_about_section(course, 'university'),
                "start-date": course.start_date_text,
            }
