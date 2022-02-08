"""
Middleware to adjust some IP/port/host request values. This is a
compatibility hack, and nothing should rely on the values this
middleware sets.
"""
from django.utils.deprecation import MiddlewareMixin

import openedx.core.djangoapps.util.ip as ip


class XForwardedForMiddleware(MiddlewareMixin):
    """
    The middleware name is now outdated, since it no longer uses a hardcoded reference
    to X-Forwarded-For.
    """

    def process_request(self, request):
        """
        Process the given request, update the value of SERVER_NAME and SERVER_PORT based
        on HTTP_HOST and X-Forwarded-Port headers
        """
        # Older code for the Gunicorn 19.0 upgrade. Original docstring:
        #
        # Gunicorn 19.0 has breaking changes for REMOTE_ADDR, SERVER_* headers
        # that can not override with forwarded and host headers.
        # This middleware can be used to update these headers set by proxy configuration.
        for field, header in [("HTTP_HOST", "SERVER_NAME"),
                              ("HTTP_X_FORWARDED_PORT", "SERVER_PORT")]:
            if field in request.META:
                request.META[header] = request.META[field]

        # This should be deleted, but is here to avoid breaking legacy
        # code. This override was previously implemented in the above
        # code by using the first IP in X-Forwarded-For, and just
        # overwrote REMOTE_ADDR, which probably creates more problems
        # elsewhere (as the full IP chain is then no longer possible
        # to construct.)
        #
        # Any code that is relying on this override should instead be
        # calling `get_client_ip` itself, which is configurable and
        # makes it possible to handle multi-valued headers correctly.
        # After that, this override can be removed.
        #
        # The ORIGINAL_REMOTE_ADDR is just there so that we can
        # actually use the remote addr in IP determination
        # code... including in this call that overwrites it!
        request.META['ORIGINAL_REMOTE_ADDR'] = request.META['REMOTE_ADDR']
        request.META['REMOTE_ADDR'] = ip.get_client_ip(request)
