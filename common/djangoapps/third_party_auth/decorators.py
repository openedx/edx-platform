"""
Decorators that can be used to interact with third_party_auth.
"""
from functools import wraps

from six.moves.urllib.parse import urlencode, urlparse

from django.conf import settings
from django.shortcuts import redirect
from django.utils.decorators import available_attrs
from django.core.urlresolvers import reverse

from third_party_auth.provider import Registry
from third_party_auth.models import LTIProviderConfig


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


def tpa_hint_ends_existing_session(func):
    """
    Modifies a view function so that, if a tpa_hint URL parameter is received, the user is
    already logged in, and the hinted SSO provider is so configured, the user is redirected
    to a logout view and then back here. When they're directed back here, a URL parameter
    called "session_cleared" will be attached to indicate that, even though a user is now
    logged in, they should be passed through without intervention.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        """
        Check for a TPA hint in combination with a logged in user, and log the user out
        if the hinted provider specifies that they should be, and if they haven't already
        been redirected to a logout by this decorator.
        """
        sso_provider = None
        provider_id = request.GET.get('tpa_hint')
        decorator_already_processed = request.GET.get('session_cleared') == 'yes'
        if provider_id and not decorator_already_processed:
            # Check that there is a provider and that we haven't already processed this view.
            if request.user and request.user.is_authenticated():
                try:
                    sso_provider = Registry.get(provider_id=provider_id)
                except ValueError:
                    sso_provider = None
        if sso_provider and sso_provider.drop_existing_session:
            # Do the redirect only if the configured provider says we ought to.
            return redirect(
                '{}?{}'.format(
                    request.build_absolute_uri(reverse('logout')),
                    urlencode(
                        {
                            'redirect_url': '{}?{}'.format(
                                request.path,
                                urlencode(
                                    [
                                        ('tpa_hint', provider_id),
                                        ('session_cleared', 'yes')
                                    ]
                                )
                            )
                        }
                    )
                )
            )

        else:
            # Otherwise, pass everything through to the wrapped view.
            return func(request, *args, **kwargs)

    return inner
