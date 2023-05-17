"""
Custom permissions for edly.
"""
from django.conf import settings
from rest_framework.permissions import BasePermission


class CanAccessEdxAPI(BasePermission):
    """
    Checks if a user can access Edx API.
    """

    def has_permission(self, request, view):
        api_key = getattr(settings, "EDX_API_KEY", None)
        if api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key:
            return True

        edly_access_user = request.user.edly_multisite_user.filter(
            sub_org__lms_site=request.site
        )
        return request.user.is_staff or bool(edly_access_user)
