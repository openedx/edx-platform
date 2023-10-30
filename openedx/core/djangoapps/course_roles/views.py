"""
Views for the course roles API.
"""
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.course_roles.helpers import get_all_user_permissions_for_a_course


@view_auth_classes()
class UserPermissionsView(APIView):

    def get(self, request):
        """
        Get all permissions for a user in a course.
        """
        user_id = self.request.query_params.get('user_id', None)
        if user_id is None:
            raise ParseError('Required user_id parameter is missing')
        course_id = self.request.query_params.get('course_id', None)
        if course_id is None:
            raise ParseError('Required course_id parameter is missing')
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise ParseError('Invalid course_id parameter')
        try:
            permissions = {
                'permissions': get_all_user_permissions_for_a_course(user_id, course_key),
            }
        except ValueError as e:
            raise NotFound(str(e))
        return Response(permissions)
