"""
Course API Authorization functions
"""

from django.contrib.auth.models import User
from rest_framework import permissions

from student.roles import GlobalStaff


class MasqueradingPermission(permissions.BasePermission):
    """
    Allow authorized users to masquerade as other users, taking on that
    user's permissions.

    This class must be listed before any other Permission classes
    to properly enable masquerading

    To masquerade as a user, add a query parameter to the URL specifying the
    masqueraded user's username:

        GET https://courses.edx.org/api/courses/v1/courses?masquerade=henry

    To use a parameter other than `masquerade`, set `masquerading_param` as a
    class attribute on any view that uses `MasqueradingPermission`.
    """

    default_masquerading_param = 'masquerade'

    def has_permission(self, request, view):
        """
        Hook for running masquerade.

        TODO: clarify what is happening
        """
        masquerading_param = getattr(view, 'masquerading_param', None) or self.default_masquerading_param
        masqueraded_username = request.query_params.get(masquerading_param, request.user.username)
        if request.user.username == masqueraded_username:
            return True
        elif self._can_masquerade(request.user):
            return self._masquerade(request, masqueraded_username)
        else:
            return False

    def _can_masquerade(self, user):
        """
        Determine whether the user has permission to masquerade as other users
        """
        staff = GlobalStaff()
        return staff.has_user(user)

    def _masquerade(self, request, username):
        """
        Enable masquerading.  The effective user is now the masqueraded one.
        """
        masqueraded_user = User.objects.get(username=username)
        if masqueraded_user:
            request.user = masqueraded_user
            return True
        else:
            return False


def can_view_courses_for_username(requesting_user, target_username):
    """
    Determine whether `requesting_user` has permission to view courses available
    to the user identified by `target_username`.

    Arguments:
        requesting_user (User): The user requesting permission to view another
        target_username (string):
            The name of the user `requesting_user` would like
            to access.

    Return value:
        Boolean:
            `True` if `requesting_user` is authorized to view courses as
            `target_username`.  Otherwise, `False`
    Raises:
        TypeError if target_username is empty or None.
    """

    # AnonymousUser has no username, so we test for requesting_user's own
    # username before prohibiting an empty target_username.
    if requesting_user.username == target_username:
        return True
    elif not target_username:
        raise TypeError("target_username must be specified")
    else:
        staff = GlobalStaff()
        return staff.has_user(requesting_user)
