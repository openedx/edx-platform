"""
Views for course info API
"""


from rest_framework import generics
from rest_framework.response import Response

from lms.djangoapps.courseware.courses import get_course_info_section_module
from openedx.core.lib.xblock_utils import get_course_update_items
from common.djangoapps.static_replace import make_static_urls_absolute

from ..decorators import mobile_course_access, mobile_view


@mobile_view()
class CourseUpdatesList(generics.ListAPIView):
    """
    **Use Case**

        Get the content for course updates.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{course_id}/updates

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
            item['content'] = apply_wrappers_to_content(item['content'], course_updates_module, request)

        return Response(updates_to_show)


@mobile_view()
class CourseHandoutsList(generics.ListAPIView):
    """
    **Use Case**

        Get the HTML for course handouts.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{course_id}/handouts

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with the following value.

        * handouts_html: The HTML for course handouts.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):
        course_handouts_module = get_course_info_section_module(request, request.user, course, 'handouts')
        if course_handouts_module:
            if course_handouts_module.data == "<ol></ol>":
                handouts_html = None
            else:
                handouts_html = apply_wrappers_to_content(course_handouts_module.data, course_handouts_module, request)
            return Response({'handouts_html': handouts_html})
        else:
            # course_handouts_module could be None if there are no handouts
            return Response({'handouts_html': None})


def apply_wrappers_to_content(content, module, request):
    """
    Updates a piece of html content with the filter functions stored in its module system, then replaces any
    static urls with absolute urls.

    Args:
        content: The html content to which to apply the content wrappers generated for this module system.
        module: The module containing a reference to the module system which contains functions to apply to the
        content. These functions include:
            * Replacing static url's
            * Replacing course url's
            * Replacing jump to id url's
        request: The request, used to replace static URLs with absolute URLs.

    Returns: A piece of html content containing the original content updated by each wrapper.

    """
    content = module.system.replace_urls(content)
    content = module.system.replace_course_urls(content)
    content = module.system.replace_jump_to_id_urls(content)

    return make_static_urls_absolute(request, content)
