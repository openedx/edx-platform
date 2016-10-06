"""
Public views
"""
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.clickjacking import xframe_options_deny
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.conf import settings

from edxmako.shortcuts import render_to_response

from openedx.core.djangoapps.external_auth.views import (
    ssl_login_shortcut,
    ssl_get_cert_from_request,
    redirect_with_get,
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

__all__ = ['signup', 'login_page', 'howitworks']


@ensure_csrf_cookie
@xframe_options_deny
def signup(request):
    """
    Display the signup form.
    """
    csrf_token = csrf(request)['csrf_token']
    if request.user.is_authenticated():
        return redirect('/course/')
    if settings.FEATURES.get('AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP'):
        # Redirect to course to login to process their certificate if SSL is enabled
        # and registration is disabled.
        return redirect_with_get('login', request.GET, False)

    return render_to_response('register.html', {'csrf': csrf_token})


@ssl_login_shortcut
@ensure_csrf_cookie
@xframe_options_deny
def login_page(request):
    """
    Display the login form.
    """
    csrf_token = csrf(request)['csrf_token']
    if (settings.FEATURES['AUTH_USE_CERTIFICATES'] and
            ssl_get_cert_from_request(request)):
        # SSL login doesn't require a login view, so redirect
        # to course now that the user is authenticated via
        # the decorator.
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('/course/')
    if settings.FEATURES.get('AUTH_USE_CAS'):
        # If CAS is enabled, redirect auth handling to there
        return redirect(reverse('cas-login'))

    return render_to_response(
        'login.html',
        {
            'csrf': csrf_token,
            'forgot_password_link': "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE),
            'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        }
    )


def howitworks(request):
    "Proxy view"
    if request.user.is_authenticated():
        return redirect('/home/')
    else:
        return render_to_response('howitworks.html', {})
