"""
Views for course info API
"""
from django.http import Http404
from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.response import Response

from courseware.courses import get_course_about_section, get_course_info_section_module
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore


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
        updates_to_show = [
            update for update in reversed(getattr(course_updates_module, 'items', []))
            if update.get("status") != "deleted"
        ]
        return Response(updates_to_show)


class CourseHandoutsList(generics.ListAPIView):
    """Please just render this in an HTML view for now.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        course_handouts_module = get_course_info_section_module(request, course, 'handouts')
        if course_handouts_module:
            return Response({'handouts_html': course_handouts_module.data})
        else:
            # course_handouts_module could be None if there are no handouts
            # (such as while running tests)
            raise Http404(u"No handouts for {}".format(unicode(course_id)))


class CourseAboutDetail(generics.RetrieveAPIView):
    """
    Renders course 'about' page
    """
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
