from rest_framework.permissions import BasePermission

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.blacklist.models import BlacklistedToken
from rest_framework_jwt.compat import gettext_lazy as _, jwt_decode

class IsNotBlacklisted(BasePermission):
    message = _('You have been blacklisted.')

    def has_permission(self, request, view):
        token = JSONWebTokenAuthentication.get_token_from_request(request)

        # Don't check the blacklist for requests with no token.
        if token is None:
            return True

        # The token should already be validated before we call this.
        payload = jwt_decode(token, None, verify=False)
        return not BlacklistedToken.is_blocked(token, payload)
