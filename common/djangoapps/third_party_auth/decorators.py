"""
Decorators that can be used to interact with third_party_auth.
"""
from functools import wraps
from urlparse import urlparse, urlunparse

from django.conf import settings
from django.utils.decorators import available_attrs

from .models import SAMLProviderData


def allow_frame_from_whitelisted_url(view_func):  # pylint: disable=invalid-name
    """
    Modifies a view function so that it can be rendered in a frame or iframe
    if parent url is whitelisted and request HTTP referrer is matches one of SAML providers's sso url.
    """

    def wrapped_view(request, *args, **kwargs):
        """ Modify the response with the correct X-Frame-Options and . """
        resp = view_func(request, *args, **kwargs)
        x_frame_option = 'DENY'
        content_security_policy = "frame-ancestors 'none'"

        if settings.FEATURES['ENABLE_THIRD_PARTY_AUTH']:
            referer = request.META.get('HTTP_REFERER')
            if referer is not None:
                parsed_url = urlparse(referer)
                # reconstruct a referer url without querystring and trailing slash
                referer_url = urlunparse(
                    (parsed_url.scheme, parsed_url.netloc, parsed_url.path.rstrip('/'), '', '', '')
                )
                sso_urls = SAMLProviderData.objects.values_list('sso_url', flat=True)
                sso_urls = [url.rstrip('/') for url in sso_urls]
                if referer_url in sso_urls:
                    allowed_urls = ' '.join(settings.THIRD_PARTY_AUTH_FRAME_ALLOWED_FROM_URL)
                    x_frame_option = 'ALLOW-FROM {}'.format(allowed_urls)
                    content_security_policy = "frame-ancestors {}".format(allowed_urls)
        resp['X-Frame-Options'] = x_frame_option
        resp['Content-Security-Policy'] = content_security_policy
        return resp
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
