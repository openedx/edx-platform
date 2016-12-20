"""
Decorators that can be used to interact with third_party_auth.
"""
from functools import wraps

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
                sso_urls = SAMLProviderData.objects.values_list('sso_url', flat=True)
                if referer in sso_urls:
                    x_frame_option = 'ALLOW-FROM %s' % settings.THIRD_PARTY_AUTH_FRAME_ALLOWED_FROM_URL
                    content_security_policy = "frame-ancestors %s" % settings.THIRD_PARTY_AUTH_FRAME_ALLOWED_FROM_URL
        resp['X-Frame-Options'] = x_frame_option
        resp['Content-Security-Policy'] = content_security_policy
        return resp
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
