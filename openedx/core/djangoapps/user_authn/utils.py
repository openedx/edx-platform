"""
Utility functions used during user authentication.
"""
from django.conf import settings
from django.utils import http


def is_safe_login_or_logout_redirect(request, redirect_to):
    """
    Determine if the given redirect URL/path is safe for redirection.
    """
    request_host = request.get_host()  # e.g. 'courses.edx.org'

    login_redirect_whitelist = set(getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []))
    login_redirect_whitelist.add(request_host)

    is_safe_url = http.is_safe_url(redirect_to, allowed_hosts=login_redirect_whitelist, require_https=True)
    return is_safe_url
