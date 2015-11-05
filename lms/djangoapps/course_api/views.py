"""
Course API Views
"""

import urllib

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from openedx.core.lib.api.view_utils import view_auth_classes


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

        blocks_url = '?'.join([
            reverse(
                'blocks_in_course',
                request=request,
            ),
            'course_id={}'.format(urllib.quote(course_key_string))
        ])

        return Response({'blocks_url': blocks_url})
