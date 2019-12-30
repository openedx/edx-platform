"""
Permissions classes for User accounts API views.
"""


from django.conf import settings
from rest_framework import permissions


class CanDeactivateUser(permissions.BasePermission):
    """
    Grants access to AccountDeactivationView if the requesting user is a superuser
    or has the explicit permission to deactivate a User account.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('student.can_deactivate_users')


class CanRetireUser(permissions.BasePermission):
    """
    Grants access to the various retirement API endpoints if the requesting user is
    a superuser, the RETIREMENT_SERVICE_USERNAME, or has the explicit permission to
    retire a User account.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_retire_user')


class CanReplaceUsername(permissions.BasePermission):
    """
    Grants access to the Username Replacement API for the service user.
    """
    def has_permission(self, request, view):
        return request.user.username == getattr(settings, "USERNAME_REPLACEMENT_WORKER", False)
