"""
Handle view-logic for the discussions app.
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import validate_course_key
from .models import DiscussionsConfiguration
from .permissions import check_course_permissions, IsStaffOrCourseTeam
from .serializers import DiscussionsConfigurationSerializer


class DiscussionsConfigurationView(APIView):
    """
    Handle configuration-related view-logic
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaffOrCourseTeam,)

    # pylint: disable=redefined-builtin
    def get(self, request, course_key_string: str, **_kwargs) -> Response:
        """
        Handle HTTP/GET requests
        """
        course_key = validate_course_key(course_key_string)
        configuration = DiscussionsConfiguration.get(course_key)
        serializer = DiscussionsConfigurationSerializer(
            configuration,
            context={
                'user_id': request.user.id,
            }
        )
        return Response(serializer.data)

    def post(self, request, course_key_string: str, **_kwargs) -> Response:
        """
        Handle HTTP/POST requests
        """
        course_key = validate_course_key(course_key_string)
        configuration = DiscussionsConfiguration.get(course_key)
        course = CourseOverview.get_from_id(course_key)
        serializer = DiscussionsConfigurationSerializer(
            configuration,
            context={
                'user_id': request.user.id,
            },
            data=request.data,
            partial=True,
        )
        if serializer.is_valid(raise_exception=True):
            new_provider_type = serializer.validated_data.get('provider_type', None)
            if new_provider_type is not None and new_provider_type != configuration.provider_type:
                check_course_permissions(course, request.user, 'change_provider')

            serializer.save()
        return Response(serializer.data)
