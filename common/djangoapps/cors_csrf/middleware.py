"""
Middleware for handling CSRF checks with CORS requests


CSRF and referrer domain checks
-------------------------------

When processing HTTPS requests, the default CSRF middleware checks that the referer
domain and protocol is the same as the request's domain and protocol. This is meant
to avoid a type of attack for sites which serve their content with both HTTP and HTTPS,
with a man in the middle on the HTTP requests.

https://github.com/django/django/blob/b91c385e324f1cb94d20e2ad146372c259d51d3b/django/middleware/csrf.py#L117

This doesn't work well with CORS requests, which aren't vulnerable to this attack when
the server from which the request is coming uses HTTPS too, as it prevents the man in the
middle attack vector.

We thus do the CSRF check of requests coming from an authorized CORS host separately
in this middleware, applying the same protections as the default CSRF middleware, but
without the referrer check, when both the request and the referer use HTTPS.


CSRF cookie domains
-------------------

In addition, in order to make cross-domain AJAX calls to CSRF-protected end-points,
we need to send the CSRF token in the HTTP header of the request.

The simple way to do this would be to set the CSRF_COOKIE_DOMAIN to ".edx.org",
but unfortunately this can cause problems.  For example, suppose that
"first.edx.org" sets the cookie with domain ".edx.org", but "second.edx.org"
sets a cookie with domain "second.edx.org".  In this case, the browser
would have two different CSRF tokens set (one for each cookie domain),
which can cause non-deterministic failures depending on which cookie
is sent first.

For this reason, we add a second cookie that (a) has the domain set to ".edx.org",
but (b) does NOT have the same name as the CSRF_COOKIE_NAME.  Clients making
cross-domain requests can use this cookie instead of the subdomain-specific
CSRF cookie.

"""

import logging
import urlparse

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured

log = logging.getLogger(__name__)


def is_cross_domain_request_allowed(request):
    """Check whether we should allow the cross-domain request.

    We allow a cross-domain request only if:

    1) The request is made securely and the referer has "https://" as the protocol.
    2) The referer domain has been whitelisted.

    Arguments:
        request (HttpRequest)

    Returns:
        bool

    """
    referer = request.META.get('HTTP_REFERER')
    referer_parts = urlparse.urlparse(referer) if referer else None
    referer_hostname = referer_parts.hostname if referer_parts is not None else None

    # Use CORS_ALLOW_INSECURE *only* for development and testing environments;
    # it should never be enabled in production.
    if not getattr(settings, 'CORS_ALLOW_INSECURE', False):
        if not request.is_secure():
            log.debug(
                u"Request is not secure, so we cannot send the CSRF token. "
                u"For testing purposes, you can disable this check by setting "
                u"`CORS_ALLOW_INSECURE` to True in the settings"
            )
            return False

        if not referer:
            log.debug(u"No referer provided over a secure connection, so we cannot check the protocol.")
            return False

        if not referer_parts.scheme == 'https':
            log.debug(u"Referer '%s' must have the scheme 'https'")
            return False

    domain_is_whitelisted = (
        getattr(settings, 'CORS_ORIGIN_ALLOW_ALL', False) or
        referer_hostname in getattr(settings, 'CORS_ORIGIN_WHITELIST', [])
    )
    if not domain_is_whitelisted:
        if referer_hostname is None:
            # If no referer is specified, we can't check if it's a cross-domain
            # request or not.
            log.debug(u"Referrer hostname is `None`, so it is not on the whitelist.")
        elif referer_hostname != request.get_host():
            log.warning(
                (
                    u"Domain '%s' is not on the cross domain whitelist.  "
                    u"Add the domain to `CORS_ORIGIN_WHITELIST` or set "
                    u"`CORS_ORIGIN_ALLOW_ALL` to True in the settings."
                ), referer_hostname
            )
        else:
            log.debug(
                (
                    u"Domain '%s' is the same as the hostname in the request, "
                    u"so we are not going to treat it as a cross-domain request."
                ), referer_hostname
            )
        return False

    return True


class CorsCSRFMiddleware(CsrfViewMiddleware):
    """
    Middleware for handling CSRF checks with CORS requests
    """
    def __init__(self):
        """Disable the middleware if the feature flag is disabled. """
        if not settings.FEATURES.get('ENABLE_CORS_HEADERS'):
            raise MiddlewareNotUsed()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """Skip the usual CSRF referer check if this is an allowed cross-domain request. """
        if not is_cross_domain_request_allowed(request):
            log.debug("Could not disable CSRF middleware referer check for cross-domain request.")
            return

        is_secure_default = request.is_secure

        def is_secure_patched():
            """
            Avoid triggering the additional CSRF middleware checks on the referrer
            """
            return False
        request.is_secure = is_secure_patched

        res = super(CorsCSRFMiddleware, self).process_view(request, callback, callback_args, callback_kwargs)
        request.is_secure = is_secure_default
        return res


class CsrfCrossDomainCookieMiddleware(object):
    """Set an additional "cross-domain" CSRF cookie.

    Usage:

        1) Decorate a view with `@ensure_csrf_cookie_cross_domain`.
        2) Set `CROSS_DOMAIN_CSRF_COOKIE_NAME` and `CROSS_DOMAIN_CSRF_COOKIE_DOMAIN`
            in settings.
        3) Add the domain to `CORS_ORIGIN_WHITELIST`
        4) Enable `FEATURES['ENABLE_CROSS_DOMAIN_CSRF_COOKIE']`

    For testing, it is often easier to relax the security checks by setting:
        * `CORS_ALLOW_INSECURE = True`
        * `CORS_ORIGIN_ALLOW_ALL = True`

    """

    def __init__(self):
        """Disable the middleware if the feature is not enabled. """
        if not settings.FEATURES.get('ENABLE_CROSS_DOMAIN_CSRF_COOKIE'):
            raise MiddlewareNotUsed()

        if not getattr(settings, 'CROSS_DOMAIN_CSRF_COOKIE_NAME', ''):
            raise ImproperlyConfigured(
                "You must set `CROSS_DOMAIN_CSRF_COOKIE_NAME` when "
                "`FEATURES['ENABLE_CROSS_DOMAIN_CSRF_COOKIE']` is True."
            )

        if not getattr(settings, 'CROSS_DOMAIN_CSRF_COOKIE_DOMAIN', ''):
            raise ImproperlyConfigured(
                "You must set `CROSS_DOMAIN_CSRF_COOKIE_DOMAIN` when "
                "`FEATURES['ENABLE_CROSS_DOMAIN_CSRF_COOKIE']` is True."
            )

    def process_response(self, request, response):
        """Set the cross-domain CSRF cookie. """

        # Check whether this is a secure request from a domain on our whitelist.
        if not is_cross_domain_request_allowed(request):
            log.debug("Could not set cross-domain CSRF cookie.")
            return response

        # Check whether (a) the CSRF middleware has already set a cookie, and
        # (b) this is a view decorated with `@ensure_cross_domain_csrf_cookie`
        # If so, we can send the cross-domain CSRF cookie.
        should_set_cookie = (
            request.META.get('CROSS_DOMAIN_CSRF_COOKIE_USED', False) and
            request.META.get('CSRF_COOKIE_USED', False) and
            request.META.get('CSRF_COOKIE') is not None
        )

        if should_set_cookie:
            # This is very similar to the code in Django's CSRF middleware
            # implementation, with two exceptions:
            # 1) We change the cookie name and domain so it can be used cross-domain.
            # 2) We always set "secure" to True, so that the CSRF token must be
            # sent over a secure connection.
            response.set_cookie(
                settings.CROSS_DOMAIN_CSRF_COOKIE_NAME,
                request.META['CSRF_COOKIE'],
                max_age=settings.CSRF_COOKIE_AGE,
                domain=settings.CROSS_DOMAIN_CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=True
            )
            log.debug(
                "Set cross-domain CSRF cookie '%s' for domain '%s'",
                settings.CROSS_DOMAIN_CSRF_COOKIE_NAME,
                settings.CROSS_DOMAIN_CSRF_COOKIE_DOMAIN
            )

        return response
