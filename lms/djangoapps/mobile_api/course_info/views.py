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
from static_replace import make_static_urls_absolute, replace_static_urls


class CourseUpdatesList(generics.ListAPIView):
    """
    **Use Case**

        Get the content for course updates.

    **Example request**:

        GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/updates

    **Response Values**

        A array of course updates. Each course update contains:

            * date: The date of the course update.

            * content: The content, as an HTML string, of the course update.

            * status: Whether the update is visible or not.

            * id: The unique identifier of the update.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        course_updates_module = get_course_info_section_module(request, course, 'updates')
        update_items = reversed(getattr(course_updates_module, 'items', []))

        updates_to_show = [
            update for update in update_items
            if update.get("status") != "deleted"
        ]

        for item in updates_to_show:
            content = item['content']
            content = replace_static_urls(
                content,
                course_id=course_id,
                static_asset_path=course.static_asset_path)
            item['content'] = make_static_urls_absolute(request, content)

        return Response(updates_to_show)


class CourseHandoutsList(generics.ListAPIView):
    """
    **Use Case**

        Get the HTML for course handouts.

    **Example request**:

        GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/handouts

    **Response Values**

        * handouts_html: The HTML for course handouts.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        course_handouts_module = get_course_info_section_module(request, course, 'handouts')
        if course_handouts_module:
            handouts_html = course_handouts_module.data
            handouts_html = replace_static_urls(
                handouts_html,
                course_id=course_id,
                static_asset_path=course.static_asset_path)
            handouts_html = make_static_urls_absolute(self.request, handouts_html)
            return Response({'handouts_html': handouts_html})
        else:
            # course_handouts_module could be None if there are no handouts
            # (such as while running tests)
            raise Http404(u"No handouts for {}".format(unicode(course_id)))


class CourseAboutDetail(generics.RetrieveAPIView):
    """
    **Use Case**

        Get the HTML for the course about page.

    **Example request**:

        GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/about

    **Response Values**

        * overview: The HTML for the course About page.
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
        about_section_html = make_static_urls_absolute(self.request, about_section_html)

        return Response(
            {"overview": about_section_html.strip() if about_section_html else ""}
        )
