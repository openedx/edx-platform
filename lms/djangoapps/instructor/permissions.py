"""
Instructor permissions for class based views
"""

from django.http import Http404
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import permissions

from courseware.access import has_access
from courseware.courses import get_course_by_id


class IsCourseStaff(permissions.BasePermission):
    """
    Check if the requesting user is a course's staff member
    """
    def has_permission(self, request, view):
        try:
            course_key = CourseKey.from_string(view.kwargs.get('course_id'))
        except InvalidKeyError:
            raise Http404()

        course = get_course_by_id(course_key)
        return has_access(request.user, 'staff', course)
