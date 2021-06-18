"""
Permissions for PakX Admin Panel APIs.
"""
from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS


class CanAccessPakXAdminPanel(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or User.objects.filter(
            groups__name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN],
            profile__organization__isnull=False,
            id=request.user.id
        ).exists()
