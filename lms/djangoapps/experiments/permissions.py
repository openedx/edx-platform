from openedx.core.lib.api import permissions


class IsStaffOrOwner(permissions.IsStaffOrOwner):
    """
    Permission that allows access to admin users or the owner of an object.
    The owner is considered the User object represented by obj.user.
    """

    def has_permission(self, request, view):
        # The view will handle filtering for the current user
        return True
