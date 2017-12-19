"""
This module provides a custom DRF Permission class for supporting SAFE_METHODS to Authenticated Users, but
requiring Superuser access for all other Request types on an API endpoint.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    """
    Method that will require staff access for all methods not
    in the SAFE_METHODS list.  For example GET requests will not
    require a Staff or Admin user.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        else:
            return request.user.is_staff
