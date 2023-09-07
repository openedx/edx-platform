"""
Helpers for the course roles app.
"""

from openedx.core.djangoapps.course_roles.models import CourseRolesUserRole
from openedx.core.lib.cache_utils import request_cached


@request_cached()
def permission_check(user, permission, course_key):
    """
    Check if a user has a permission.
    """
    pass
    return CourseRolesUserRole.objects.filter(
        user=user,
        role__permissions__name=permission,
        course=course_key,
    ).exists()
