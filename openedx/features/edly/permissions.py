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

        return request.user.is_staff or \
            request.site.edly_sub_org_for_lms.slug in request.user.edly_profile.get_linked_edly_sub_organizations
