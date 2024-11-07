"""
Permissions for notifications
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.permissions import IsAuthenticated

from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


def allow_any_authenticated_user():
    """
    Function and class decorator that abstracts the authentication and permission checks for api views.
    Allows both verified and non-verified users
    """
    def _decorator(func_or_class):
        """
        Requires either OAuth2 or Session-based authentication.
        """
        func_or_class.authentication_classes = (
            JwtAuthentication,
            BearerAuthenticationAllowInactiveUser,
            SessionAuthenticationAllowInactiveUser
        )
        func_or_class.permission_classes = (IsAuthenticated,)
        return func_or_class
    return _decorator
