"""
Custom permissions for the content store views.
"""

from rest_framework.permissions import BasePermission

from opaque_keys.edx.keys import CourseKey
from common.djangoapps.student.auth import has_studio_write_access


class HasStudioWriteAccess(BasePermission):
    """
    Custom permission to check if the user has studio write access to the course.
    Expects the view to have a `course_key_string` kwarg or attribute.
    """
    def has_permission(self, request, view):
        course_key_string = view.kwargs.get('course_key_string')
        if not course_key_string:
            # Try to get from view attribute (for APIView)
            course_key_string = getattr(view, 'course_key_string', None)
        if not course_key_string:
            return False

        course_key = CourseKey.from_string(course_key_string)

        if not has_studio_write_access(request.user, course_key):
            return False

        return True
