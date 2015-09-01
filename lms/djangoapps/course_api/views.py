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
    View class for the Course API
    """
    def get(self, request, course_key_string):
        course_key = CourseKey.from_string(course_key_string)
        course_usage_key = modulestore().make_course_usage_key(course_key)

        return Response({
            'blocks_url': reverse(
                'course_blocks',
                kwargs={'usage_key_string': unicode(course_usage_key)},
                request=request,
            )
        })
