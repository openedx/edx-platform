"""
This module provides a custom DRF Permission class for supporting SAFE_METHODS to Authenticated Users, but
requiring Superuser access for all other Request types on an API endpoint.
"""


from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

from lms.djangoapps.courseware.access import has_access


class IsAdminOrSupportOrAuthenticatedReadOnly(BasePermission):
    """
    Method that will require admin or support access for all methods not
    in the SAFE_METHODS list.  For example GET requests will not
    require an Admin or Support user.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        else:
            return request.user.is_staff or has_access(request.user, "support", "global")


class IsSubscriptionWorkerUser(BasePermission):
    """
    Method that will require the request to be coming from the subscriptions service worker user.
    """

    def has_permission(self, request, view):
        return request.user.username == settings.SUBSCRIPTIONS_SERVICE_WORKER_USERNAME
