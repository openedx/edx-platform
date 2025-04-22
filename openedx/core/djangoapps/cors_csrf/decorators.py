"""Decorators for cross-domain CSRF. """


from django.views.decorators.csrf import ensure_csrf_cookie
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser
)  # lint-amnesty, pylint: disable=wrong-import-order


def ensure_csrf_cookie_cross_domain(func):
    """View decorator for sending a cross-domain CSRF cookie.

    This works like Django's `@ensure_csrf_cookie`, but
    additionally checks request.successful_authenticator for cases where
    multiple authentication classes are involved in a view.

    Arguments:
        func (function): The view function to decorate.

    """
    def _inner(*args, **kwargs):  # pylint: disable=missing-docstring
        if args:
            request = args[0]

            # if the successful_authenticator is an instance of SessionAuthenticationAllowInactiveUser
            # it's safe to ensure the CSRF cookie is included.
            if isinstance(request.successful_authenticator, SessionAuthenticationAllowInactiveUser):
                return ensure_csrf_cookie(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return _inner
