"""
Permissions for cohorts API
"""

from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions

from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_MODERATOR
)
from common.djangoapps.student.roles import GlobalStaff
from lms.djangoapps.discussion.django_comment_client.utils import get_user_role_names


class IsStaffOrAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is staff or an admin.
    """

    def has_permission(self, request, view):
        """Returns true if the user is admin or staff and request method is GET."""
        course_key = CourseKey.from_string(view.kwargs.get('course_key_string'))
        user_roles = get_user_role_names(request.user, course_key)
        is_user_staff = bool(user_roles & {
            FORUM_ROLE_ADMINISTRATOR,
            FORUM_ROLE_MODERATOR,
            FORUM_ROLE_COMMUNITY_TA,
        })
        return (
            GlobalStaff().has_user(request.user) or
            request.user.is_staff or
            is_user_staff and request.method == "GET"
        )
