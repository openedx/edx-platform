"""Appsembler custom views for Studio

Views here provide Studio local login/logout
"""

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from django.utils.decorators import method_decorator

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.views.login import _get_user_by_email

from edxmako.shortcuts import render_to_response


def forgot_password_link():
    return "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE)


def platform_name():
    return configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)


def render_login_page(show_login_error_message=False):
    """Convenience function to put the login page

    Arguments:
        show_login_error_message (bool): flag to show if a login attempt failed

    Returns:
        django.http.response.HttpResponse object with the login page content
    """
    return render_to_response(
        'login_page.html',
        {
            'show_login_error_message': show_login_error_message,
            'forgot_password_link': forgot_password_link(),
            'platform_name': platform_name(),
        }
    )


class LoginView(View):
    """Basic login view to allow for Studio local logins
    """

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(xframe_options_deny)
    def get(self, request):
        return render_login_page()

    @method_decorator(ensure_csrf_cookie)
    def post(self, request, *args, **kwargs):
        user = _get_user_by_email(request)
        password = request.POST['password']

        if user:
            user = authenticate(request, username=user.username, password=password)

        if not user:
            return render_login_page(show_login_error_message=True)

        login(request, user)
        return redirect(reverse('home'))
