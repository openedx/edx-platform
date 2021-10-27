"""
Handle view-logic for the djangoapp
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.roles import CourseStaffRole, GlobalStaff
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import validate_course_key
from .models import DiscussionsConfiguration
from .serializers import DiscussionsConfigurationSerializer


class IsStaff(BasePermission):
    """
    Check if user is global or course staff

    We create our own copy of this because other versions of this check
    allow access to additional user roles.
    """

    def has_permission(self, request, view):
        """
        Check if user has global or course staff permission
        """
        user = request.user
        if user.is_staff:
            return True
        course_key_string = view.kwargs.get('course_key_string')
        course_key = validate_course_key(course_key_string)
        return CourseStaffRole(
            course_key,
        ).has_user(request.user)


def user_permissions_for_course(course, user):
    """
    Return the user's permissions over the discussion configuration of the course.
    """
    return {
        "change_provider": not course.has_started() or GlobalStaff().has_user(user),
    }

PERMISSION_MESSAGES = {
    "change_provider": "Must be global staff to change discussion provider after the course has started.",
}

DEFAULT_MESSAGE = "You're not authorized to perform this operation."


def check_course_permissions(course, user, permission):
    """
    Check the user has permissions for the operation over the course configuration.

    Raises PermissionDenied if the user does not have permission
    """
    permissions = user_permissions_for_course(course, user)
    granted = permissions.get(permission)
    if not granted:
        raise PermissionDenied(PERMISSION_MESSAGES.get(permission, DEFAULT_MESSAGE))


class DiscussionsConfigurationView(APIView):
    """
    Handle configuration-related view-logic
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaff,)

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
            if serializer.validated_data['provider_type'] != configuration.provider_type:
                check_course_permissions(course, request.user, 'change_provider')

            serializer.save()
        return Response(serializer.data)
