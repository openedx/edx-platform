"""
Views for the offline_mode app.
"""
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.authentication import BearerAuthentication
from .tasks import generate_offline_content_for_course
from .toggles import is_offline_mode_enabled


class SudioCoursePublishedEventHandler(APIView):
    """
    Handle the event of a course being published in Studio.

    This view is called by Studio when a course is published,
    and it triggers the generation of offline content.
    """

    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication)
    permission_classes = (IsAdminUser,)

    def post(self, request, *args, **kwargs):
        """
        Trigger the generation of offline content task.
        Args:
            request (Request): The incoming request object.
            args: Additional positional arguments.
            kwargs: Additional keyword arguments.
        Returns:
            Response: The response object.
        """
        course_id = request.data.get('course_id')
        if not course_id:
            return Response(
                data={'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return Response(
                data={'error': 'Invalid course_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if is_offline_mode_enabled(course_key):
            generate_offline_content_for_course.apply_async(args=[course_id])
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                data={'error': 'Offline mode is not enabled for this course'},
                status=status.HTTP_400_BAD_REQUEST,
            )
