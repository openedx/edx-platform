"""Decorators for cross-domain CSRF. """


from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication


def ensure_csrf_cookie_cross_domain(func):
    """View decorator for sending a cross-domain CSRF cookie.

    This works like Django's `@ensure_csrf_cookie`, but
    additionally checks request.successful_authenticator to determine if
    it is derived from rest_framework.authentication.SessionAuthentication
    If so, the CSRF cookie is added.

    Arguments:
        func (function): The view function to decorate.

    """
    def _inner(*args, **kwargs):  # pylint: disable=missing-docstring
        if args:
            request = args[0]
            current_authenticator = getattr(request, 'successful_authenticator', None)

            # if the current_authenticator is an instance or derived from
            # rest_framework.authentication.SessionAuthentication
            # it's safe to ensure the CSRF cookie is included.
            if current_authenticator and isinstance(current_authenticator, SessionAuthentication):
                return ensure_csrf_cookie(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return _inner
