"""
This module provides a custom DRF Permission class for supporting the e2e
testing.
"""
from django.conf import settings
from rest_framework.permissions import BasePermission


class IsE2eTestUser(BasePermission):
    """
    Method that will ensure whether the requesting user is e2e
    test user or not
    """
    def has_permission(self, request, view):
        # check whether requesting user is the e2e test user or not
        return request.user.username == settings.E2E_TEST_USER_USERNAME
