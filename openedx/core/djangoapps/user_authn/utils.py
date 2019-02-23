"""
Utility functions used during user authentication.
"""
from django.conf import settings
from django.utils import http
from oauth2_provider.models import Application
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error


def is_safe_login_or_logout_redirect(request, redirect_to):
    """
    Determine if the given redirect URL/path is safe for redirection.
    """
    login_redirect_whitelist = set(getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []))

    request_host = request.get_host()  # e.g. 'courses.edx.org'
    login_redirect_whitelist.add(request_host)

    # Allow OAuth2 clients to redirect back to their site after logout.
    dot_client_id = request.GET.get('client_id')
    if dot_client_id:
        application = Application.objects.get(client_id=dot_client_id)
        if redirect_to in application.redirect_uris:
            login_redirect_whitelist.add(urlparse(redirect_to).netloc)

    is_safe_url = http.is_safe_url(
        redirect_to, allowed_hosts=login_redirect_whitelist, require_https=request.is_secure(),
    )
    return is_safe_url
