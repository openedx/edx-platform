"""
Custom permissions for edly.
"""
from rest_framework.permissions import BasePermission


class CanAccessEdxAPI(BasePermission):
    """
    Checks if a user can access Edx API.
    """

    def has_permission(self, request, view):
        return request.user.is_staff or \
            request.site.edly_sub_org_for_lms.slug in request.user.edly_profile.get_linked_edly_sub_organizations
