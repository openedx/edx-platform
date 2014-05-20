from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from courseware.courses import get_course_about_section, get_course_info_section_module
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
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        course_updates_module = get_course_info_section_module(request, course, 'updates')
        return Response(reversed(course_updates_module.items))


class CourseHandoutsList(generics.ListAPIView):
    """Please just render this in an HTML view for now.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        course_handouts_module = get_course_info_section_module(request, course, 'handouts')
        return Response({'handouts_html': course_handouts_module.data})


class CourseAboutDetail(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)

        # There are other fields, but they don't seem to be in use.
        # see courses.py:get_course_about_section.
        #
        # This can also return None, so check for that before calling strip()
        about_section_html = get_course_about_section(course, "overview")
        return Response(
            {"overview": about_section_html.strip() if about_section_html else ""}
        )
