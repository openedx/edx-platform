"""
Permissions for PakX Admin Panel APIs.
"""
from rest_framework.permissions import BasePermission
from .constants import GROUP_TRAINING_MANAGERS


class CanAccessPakXAdminPanel(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(
            name=GROUP_TRAINING_MANAGERS
        ).exists()
