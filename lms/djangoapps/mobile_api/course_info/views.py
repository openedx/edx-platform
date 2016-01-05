"""
Views for course info API
"""
from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response

from courseware.courses import get_course_info_section_module
from static_replace import make_static_urls_absolute, replace_static_urls
from openedx.core.lib.xblock_utils import get_course_update_items

from ..utils import mobile_view, mobile_course_access


@mobile_view()
class CourseUpdatesList(generics.ListAPIView):
    """
    **Use Case**

        Get the content for course updates.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/updates

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with an array of course updates. Each course update
        contains the following values.

            * content: The content, as an HTML string, of the course update.
            * date: The date of the course update.
            * id: The unique identifier of the update.
            * status: Whether the update is visible or not.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):
        course_updates_module = get_course_info_section_module(request, request.user, course, 'updates')
        update_items = get_course_update_items(course_updates_module)

        updates_to_show = [
            update for update in update_items
            if update.get("status") != "deleted"
        ]

        for item in updates_to_show:
            content = item['content']
            content = replace_static_urls(
                content,
                course_id=course.id,
                static_asset_path=course.static_asset_path)
            item['content'] = make_static_urls_absolute(request, content)

        return Response(updates_to_show)


@mobile_view()
class CourseHandoutsList(generics.ListAPIView):
    """
    **Use Case**

        Get the HTML for course handouts.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/handouts

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with the following value.

        * handouts_html: The HTML for course handouts.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):
        course_handouts_module = get_course_info_section_module(request, request.user, course, 'handouts')
        if course_handouts_module:
            handouts_html = course_handouts_module.data
            handouts_html = replace_static_urls(
                handouts_html,
                course_id=course.id,
                static_asset_path=course.static_asset_path)
            handouts_html = make_static_urls_absolute(self.request, handouts_html)
            return Response({'handouts_html': handouts_html})
        else:
            # course_handouts_module could be None if there are no handouts
            raise Http404(u"No handouts for {}".format(unicode(course.id)))
