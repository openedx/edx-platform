"""
Decorators that can be used to interact with third_party_auth.
"""
from functools import wraps
from urlparse import urlparse

from django.conf import settings
from django.utils.decorators import available_attrs

from third_party_auth.models import SAMLProviderData
from third_party_auth.models import LTIProviderConfig


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
                sso_urls = SAMLProviderData.objects.values_list('sso_url', flat=True)
                if referer in sso_urls:
                    allowed_urls = ' '.join(settings.THIRD_PARTY_AUTH_FRAME_ALLOWED_FROM_URL)
                    x_frame_option = 'ALLOW-FROM {}'.format(allowed_urls)
                    content_security_policy = "frame-ancestors {}".format(allowed_urls)
        resp['X-Frame-Options'] = x_frame_option
        resp['Content-Security-Policy'] = content_security_policy
        return resp
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


def xframe_allow_whitelisted(view_func):
    """
    Modifies a view function so that its response has the X-Frame-Options HTTP header
    set to 'DENY' if the request HTTP referrer is not from a whitelisted hostname.
    """

    def wrapped_view(request, *args, **kwargs):
        """ Modify the response with the correct X-Frame-Options. """
        resp = view_func(request, *args, **kwargs)
        x_frame_option = 'DENY'
        if settings.FEATURES['ENABLE_THIRD_PARTY_AUTH']:
            referer = request.META.get('HTTP_REFERER')
            if referer is not None:
                parsed_url = urlparse(referer)
                hostname = parsed_url.hostname
                if LTIProviderConfig.objects.current_set().filter(lti_hostname=hostname, enabled=True).exists():
                    x_frame_option = 'ALLOW'
        resp['X-Frame-Options'] = x_frame_option
        return resp
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
