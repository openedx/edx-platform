"""
Views for the course roles API.
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.course_roles.api import (
    get_all_user_permissions_for_a_course,
)
from openedx.core.djangoapps.course_roles.toggles import use_permission_checks


@view_auth_classes()
class UserPermissionsView(APIView):
    """
    View for getting all permissions for a user in a course.
    """
    def get(self, request):
        """
        Get all permissions for a user in a course.

        **Permissions**: User must be authenticated.
        **Response Format**:
        ```json
        {
            "permissions": [(str) permission_name, ...]
        }
        ```
        **Response Error Codes**:
        - 400: If the user_id or course_id parameters are missing or are invalid.
        - 404: If the user or course does not exist.
        """
        user_id = self.request.query_params.get('user_id')
        if user_id is None:
            raise ParseError('Required user_id parameter is missing')
        course_id = self.request.query_params.get('course_id')
        if course_id is None:
            raise ParseError('Required course_id parameter is missing')
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError as exc:
            raise ParseError(f'Invalid course_id: {course_id}') from exc
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise NotFound(str(exc)) from exc
        try:
            permissions_set = get_all_user_permissions_for_a_course(user, course_key)
            permissions = {
                'permissions': {permission.value.name for permission in permissions_set},
            }
        except ValueError as exc:
            raise NotFound(str(exc)) from exc
        return Response(permissions)


@view_auth_classes()
class UserPermissionsFlagView(APIView):
    """
    View for getting the permission_checks waffle flag value
    """

    def get(self, request):
        """
        Get endpoint to explose whether the permission_check_flag is enabled
        **Permissions**: User must be authenticated.
        **Response Format**:
        ```json
        {
            "enabled": bool
        }
        ```
        """
        payload = {'enabled': use_permission_checks()}
        return Response(payload)
