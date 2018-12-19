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
    login_redirect_whitelist.extend(get_lms_and_cms_hosts(request))
    login_redirect_whitelist.extend(_get_oauth2_client_allowed_redirect_url(request))

    is_safe_url = http.is_safe_url(
        redirect_to, allowed_hosts=login_redirect_whitelist, require_https=request.is_secure(),
    )
    return is_safe_url


def get_lms_and_cms_hosts(request):
    return [
        login_redirect_whitelist.add(request.get_host())
        login_redirect_whitelist.add(settings.CMS_BASE)
    ]


def _get_oauth2_client_allowed_redirect_url(request, redirect_to):
   # Allow OAuth2 clients to redirect back to their site after logout.
    dot_client_id = request.GET.get('client_id')
    if dot_client_id:
        application = Application.objects.get(client_id=dot_client_id)
        if redirect_to in application.redirect_uris:
            return [urlparse(redirect_to).netloc]
    return []
