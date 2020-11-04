"""
Experimentation permissions
"""


from rest_framework.permissions import SAFE_METHODS, BasePermission

from openedx.core.lib.api import permissions


class IsStaffOrOwner(permissions.IsStaffOrOwner):
    """
    Permission that allows access to admin users or the owner of an object.
    The owner is considered the User object represented by obj.user.
    """

    def has_permission(self, request, view):
        # Staff users can create data for anyone.
        # Non-staff users can only create data for themselves.
        if view.action == 'create':
            username = request.user.username
            return super(IsStaffOrOwner, self).has_permission(request, view) or (
                username == request.data.get('user', username))

        # The view will handle filtering for the current user
        return True


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS


class IsStaffOrReadOnlyForSelf(BasePermission):
    """
    Grants access to staff or to user reading info about their own user
    """
    def has_permission(self, request, view):
        username = request.user.username
        return request.user.is_staff or (request.method in SAFE_METHODS and (
            username == request.parser_context['kwargs']['username']))
