from django_future.csrf import ensure_csrf_cookie
from django.core.context_processors import csrf
from django.shortcuts import redirect
from django.conf import settings

from mitxmako.shortcuts import render_to_response

from external_auth.views import ssl_login_shortcut
from .user import index

__all__ = ['signup', 'old_login_redirect', 'login_page', 'howitworks']

"""
Public views
"""


@ensure_csrf_cookie
def signup(request):
    """
    Display the signup form.
    """
    csrf_token = csrf(request)['csrf_token']
    return render_to_response('signup.html', {'csrf': csrf_token})


def old_login_redirect(request):
    '''
    Redirect to the active login url.
    '''
    return redirect('login', permanent=True)


@ssl_login_shortcut
@ensure_csrf_cookie
def login_page(request):
    """
    Display the login form.
    """
    csrf_token = csrf(request)['csrf_token']
    return render_to_response('login.html', {
        'csrf': csrf_token,
        'forgot_password_link': "//{base}/#forgot-password-modal".format(base=settings.LMS_BASE),
    })


def howitworks(request):
    if request.user.is_authenticated():
        return index(request)
    else:
        return render_to_response('howitworks.html', {})
