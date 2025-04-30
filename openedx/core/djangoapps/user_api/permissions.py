"""
Permissions classes for User-API aware views.
"""

from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from openedx.core.djangoapps.user_api.accounts.api import visible_fields


def is_field_shared_factory(field_name):
    """
    Generates a permission class that grants access if a particular profile field is
    shared with the requesting user.
    """

    class IsFieldShared(permissions.BasePermission):
        """
        Grants access if a particular profile field is shared with the requesting user.
        """
        def has_permission(self, request, view):
            url_username = request.parser_context.get('kwargs', {}).get('username', '')
            if request.user.username.lower() == url_username.lower():
                return True
            # Staff can always see profiles.
            if request.user.is_staff:
                return True
            # This should never return Multiple, as we don't allow case name collisions on registration.
            user = get_object_or_404(User, username__iexact=url_username)
            if field_name in visible_fields(user.profile, user):
                return True
            raise Http404()

    return IsFieldShared


class TokenPermission(permissions.BasePermission):
    """
    Allow access if
        - Token matches in Authorization header with the token in settings
        - No token is present in settings

    How to use:
        - Add the following line in class view
            token_name = "my_token_name"
        - In settings.py add the following line
            API_TOKEN = { "my_token_name": "token_value"}
    """

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization', "")
        expected_token = getattr(settings, "API_TOKEN", {}).get(getattr(view, "token_name", ""), "")

        if auth_header == expected_token:
            return True

        raise PermissionDenied(detail="Invalid or missing token.")
