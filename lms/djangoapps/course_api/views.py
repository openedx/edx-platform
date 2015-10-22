"""
Course API Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore

from .api import (
    list_courses,
    course_view
)

@view_auth_classes()
class CourseView(APIView):
    """
    View class for the Course API
    """
    def get(self, request, course_key_string):

        return (course_view(request, course_key_string))

class CourseListView(APIView):
    """
    View class to list courses
    """
    def get(self, request):

        username = request.query_params.get('user', '')

        return (list_courses(request, username))
