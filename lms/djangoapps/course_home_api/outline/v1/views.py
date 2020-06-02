"""
Outline Tab Views
"""


from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edx_django_utils import monitoring as monitoring_utils
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_home_api.outline.v1.serializers import OutlineTabSerializer
from openedx.features.course_experience.course_tools import CourseToolsPluginManager


class OutlineTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Outline Tab

    **Example Requests**

        GET api/course_home/v1/outline/{course_key}

    **Response Values**

        Body consists of the following fields:

        course_tools: List of serialized Course Tool objects. Each serialization has the following fields:
            analytics_id: (str) The unique id given to the tool
            title: (str) The display title of the tool
            url: (str) The link to access the tool

    **Returns**

        * 200 on success with above fields.
        * 403 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.

    """

    permission_classes = (IsAuthenticated,)
    serializer_class = OutlineTabSerializer

    def get(self, request, course_key_string):
        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_metric('course_id', course_key_string)
        monitoring_utils.set_custom_metric('user_id', request.user.id)
        monitoring_utils.set_custom_metric('is_staff', request.user.is_staff)

        course_key = CourseKey.from_string(course_key_string)
        course_tools = CourseToolsPluginManager.get_enabled_course_tools(request, course_key)

        data = {
            'course_tools': course_tools,
        }
        context = self.get_serializer_context()
        context['course_key'] = course_key
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)
