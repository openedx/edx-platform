"""
Public views
"""
from __future__ import absolute_import

from django.conf import settings
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.utils.http import urlquote_plus
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import ensure_csrf_cookie
from waffle.decorators import waffle_switch

from contentstore.config import waffle
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

__all__ = ['signup', 'login_page', 'login_redirect_to_lms', 'howitworks', 'accessibility']


@ensure_csrf_cookie
@xframe_options_deny
def signup(request):
    """
    Display the signup form.
    """
    csrf_token = csrf(request)['csrf_token']
    if request.user.is_authenticated:
        return redirect('/course/')

    return render_to_response('register.html', {'csrf': csrf_token})


@ensure_csrf_cookie
@xframe_options_deny
def login_page(request):
    """
    Display the login form.
    """
    csrf_token = csrf(request)['csrf_token']

    return render_to_response(
        'login.html',
        {
            'csrf': csrf_token,
            'forgot_password_link': "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE),
            'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        }
    )


def login_redirect_to_lms(request):
    """
    This view redirects to the LMS login view. It is used for Django's LOGIN_URL
    setting, which is where unauthenticated requests to protected endpoints are redirected.
    """
    next_url = request.GET.get('next')
    absolute_next_url = request.build_absolute_uri(next_url)
    login_url = '{base_url}/login{params}'.format(
        base_url=settings.LMS_ROOT_URL,
        params='?next=' + urlquote_plus(absolute_next_url) if next_url else '',
    )
    return redirect(login_url)


def howitworks(request):
    "Proxy view"
    if request.user.is_authenticated:
        return redirect('/home/')
    else:
        return render_to_response('howitworks.html', {})


@waffle_switch('{}.{}'.format(waffle.WAFFLE_NAMESPACE, waffle.ENABLE_ACCESSIBILITY_POLICY_PAGE))
def accessibility(request):
    """
    Display the accessibility accommodation form.
    """

    return render_to_response('accessibility.html', {
        'language_code': request.LANGUAGE_CODE
    })
