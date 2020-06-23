"""
Utility functions used during user authentication.
"""


import random
import string

from django.conf import settings
from django.utils import http
from oauth2_provider.models import Application
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error


def is_safe_login_or_logout_redirect(redirect_to, request_host, dot_client_id, require_https):
    """
    Determine if the given redirect URL/path is safe for redirection.

    Arguments:
        redirect_to (str):
            The URL in question.
        request_host (str):
            Originating hostname of the request.
            This is always considered an acceptable redirect target.
        dot_client_id (str|None):
            ID of Django OAuth Toolkit client.
            It is acceptable to redirect to any of the DOT client's redirct URIs.
            This argument is ignored if it is None.
        require_https (str):
            Whether HTTPs should be required in the redirect URL.

    Returns: bool
    """
    login_redirect_whitelist = set(getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []))
    login_redirect_whitelist.add(request_host)

    # Allow OAuth2 clients to redirect back to their site after logout.
    if dot_client_id:
        application = Application.objects.get(client_id=dot_client_id)
        if redirect_to in application.redirect_uris:
            login_redirect_whitelist.add(urlparse(redirect_to).netloc)

    is_safe_url = http.is_safe_url(
        redirect_to, allowed_hosts=login_redirect_whitelist, require_https=require_https
    )
    return is_safe_url


def generate_password(length=12, chars=string.ascii_letters + string.digits):
    """Generate a valid random password"""
    if length < 8:
        raise ValueError("password must be at least 8 characters")

    choice = random.SystemRandom().choice

    password = ''
    password += choice(string.digits)
    password += choice(string.ascii_letters)
    password += ''.join([choice(chars) for _i in range(length - 2)])
    return password
