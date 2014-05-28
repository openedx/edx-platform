"""
Middleware for handling CSRF checks with CORS requests

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
"""

import logging
import urlparse

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware

log = logging.getLogger(__name__)


class CorsCSRFMiddleware(CsrfViewMiddleware):
    def is_enabled(self, request):
        if not settings.FEATURES.get('ENABLE_CORS_HEADERS'):
            return False

        referer = request.META.get('HTTP_REFERER')
        if referer is None or referer == '':
            return False
        referer_parts = urlparse.urlparse(referer)

        if referer_parts.hostname not in getattr(settings, 'CORS_ORIGIN_WHITELIST', []):
            return False
        if not request.is_secure() or referer_parts.scheme != 'https':
            return False

        return True

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not self.is_enabled(request):
            return

        is_secure_default = request.is_secure
        def is_secure_patched():
            return False
        request.is_secure = is_secure_patched

        res = super(CorsCSRFMiddleware, self).process_view(request, callback, callback_args, callback_kwargs)
        request.is_secure = is_secure_default
        return res
