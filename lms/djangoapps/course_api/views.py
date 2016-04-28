"""
Course API Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore


@view_auth_classes()
class CourseView(APIView):
    """
    Course API view
    """

    def get(self, request, course_key_string):
        """
        Request information on a course specified by `course_key_string`.
            Body consists of a `blocks_url` that can be used to fetch the
            blocks for the requested course.

        Arguments:
            request (HttpRequest)
            course_key_string

        Returns:
            HttpResponse: 200 on success


        Example Usage:

            GET /api/courses/v1/[course_key_string]
            200 OK

        Example response:

            {"blocks_url": "https://server/api/courses/v1/blocks/[usage_key]"}
        """

        course_key = CourseKey.from_string(course_key_string)
        course_usage_key = modulestore().make_course_usage_key(course_key)

        blocks_url = reverse(
            'blocks_in_block_tree',
            kwargs={'usage_key_string': unicode(course_usage_key)},
            request=request,
        )

        return Response({'blocks_url': blocks_url})
