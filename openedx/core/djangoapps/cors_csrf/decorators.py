"""Decorators for cross-domain CSRF. """
from django.views.decorators.csrf import ensure_csrf_cookie


def ensure_csrf_cookie_cross_domain(func):
    """View decorator for sending a cross-domain CSRF cookie.

    This works like Django's `@ensure_csrf_cookie`, but
    will also set an additional CSRF cookie for use
    cross-domain.

    Arguments:
        func (function): The view function to decorate.

    """
    def _inner(*args, **kwargs):  # pylint: disable=missing-docstring
        if args:
            # Set the META `CROSS_DOMAIN_CSRF_COOKIE_USED` flag so
            # that `CsrfCrossDomainCookieMiddleware` knows to set
            # the cross-domain version of the CSRF cookie.
            request = args[0]
            request.META['CROSS_DOMAIN_CSRF_COOKIE_USED'] = True

        # Decorate the request with Django's
        # `ensure_csrf_cookie` to ensure that the usual
        # CSRF cookie gets set.
        return ensure_csrf_cookie(func)(*args, **kwargs)
    return _inner
