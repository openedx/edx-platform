"""
Permissions classes for User accounts API views.
"""
from __future__ import unicode_literals

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
        return (
            request.user.username == settings.RETIREMENT_SERVICE_WORKER_USERNAME or
            request.user.is_superuser
        )
