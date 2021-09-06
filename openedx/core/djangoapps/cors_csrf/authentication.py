"""
Django Rest Framework Authentication classes for cross-domain end-points.
"""


from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import authentication

from .helpers import is_cross_domain_request_allowed, skip_cross_domain_referer_check


class SessionAuthenticationCrossDomainCsrf(authentication.SessionAuthentication):
    """
    Session authentication that skips the referer check over secure connections.

    Django Rest Framework's `SessionAuthentication` class calls Django's
    CSRF middleware implementation directly, which bypasses the middleware
    stack.

    This version of `SessionAuthentication` performs the same workaround
    as `CorsCSRFMiddleware` to skip the referer check for whitelisted
    domains over a secure connection.  See `cors_csrf.middleware` for
    more information.

    Since this subclass overrides only the `enforce_csrf()` method,
    it can be mixed in with other `SessionAuthentication` subclasses.
    """
    def _process_enforce_csrf(self, request):
        CsrfViewMiddleware().process_request(request)
        return super(SessionAuthenticationCrossDomainCsrf, self).enforce_csrf(request)

    def enforce_csrf(self, request):
        """
        Skip the referer check if the cross-domain request is allowed.
        """
        if is_cross_domain_request_allowed(request):
            with skip_cross_domain_referer_check(request):
                return self._process_enforce_csrf(request)
        else:
            return self._process_enforce_csrf(request)
