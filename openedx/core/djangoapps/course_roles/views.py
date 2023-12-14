"""
Views for the course roles API.
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from rest_framework.exceptions import ParseError, PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.course_roles.api import (
    get_all_user_permissions_for_a_course,
)
from openedx.core.djangoapps.course_roles.toggles import use_permission_checks
from openedx.core.lib.exceptions import CourseNotFoundError


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
        # TODO: At the moment we only allow users to get their own permissions.
        # This will change in the future, and will be implemented with proper permission validation.
        if int(user_id) != int(self.request.user.id):
            raise PermissionDenied('You do not have access to this resource')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise NotFound(f'user_id: {user_id} not found') from exc
        try:
            permissions_set = get_all_user_permissions_for_a_course(user, course_key)
        except CourseNotFoundError as exc:
            raise NotFound(f'course_key: {course_key} not found') from exc
        permissions = {
                'user_id': user_id,
                'course_key': str(course_key),
                'permissions': {permission.value.name for permission in permissions_set},
            }
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
