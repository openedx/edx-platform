"""
Permissions classes for User accounts API views.
"""
from __future__ import unicode_literals

from rest_framework import permissions


class CanDeactivateUser(permissions.BasePermission):
    """
    Grants access to AccountDeactivationView if the requesting user is a superuser
    or has the explicit permission to deactivate a User account.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('student.can_deactivate_users')
