from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from courseware.courses import get_course_about_section
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment, User


class CourseUpdatesList(generics.ListAPIView):
    """Notes:

    1. This only works for new-style course updates and is not the older freeform
       format.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        # This parsing is horrible. Find out how we're supposed to do this properly.
        course_id = CourseKey.from_string(kwargs['course_id'])
        course_updates_module = get_course_info_module(request, course_id, 'updates')
        return Response(reversed(course_updates_module.items))


class CourseHandoutsList(generics.ListAPIView):
    """Please just render this in an HTML view for now.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course_handouts_module = get_course_info_module(request, course_id, 'handouts')
        return Response({'handouts_html': course_handouts_module.data})


class CourseAboutDetail(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)

        # There are other fields, but they don't seem to be in use.
        # see courses.py:get_course_about_section
        return Response(
            {"overview": get_course_about_section(course, "overview").strip()}
        )


def get_course_info_module(request, course_id, section_key):
    """Return the appropriate course info module (updates or handouts).

    Args:
        request: Django Request object
        course_id (CourseKey): The CourseKey for the course.
        section_key (str): Either "updates" or "handouts"

    """
    course = modulestore().get_course(course_id)
    usage_key = course_id.make_usage_key('course_info', section_key)

    # Empty cache
    field_data_cache = FieldDataCache([], course_id, request.user)

    return get_module(
        request.user,
        request,
        usage_key,
        field_data_cache,

        # We're not running JS on this page, so no need to wrap it in a div
        wrap_xmodule_display=False,

        # Needed because section modules aren't children of Course and don't
        # automatically inherit this value.
        static_asset_path=course.static_asset_path
    )
