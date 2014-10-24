"""Helpers for the student app. """
import time
from django.utils.http import cookie_date
from django.conf import settings


def set_logged_in_cookie(request, response):
    """Set a cookie indicating that the user is logged in.

    Some installations have an external marketing site configured
    that displays a different UI when the user is logged in
    (e.g. a link to the student dashboard instead of to the login page)

    Arguments:
        request (HttpRequest): The request to the view, used to calculate
            the cookie's expiration date based on the session expiration date.
        response (HttpResponse): The response on which the cookie will be set.

    Returns:
        HttpResponse

    """
    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
        expires_time = time.time() + max_age
        expires = cookie_date(expires_time)

    response.set_cookie(
        settings.EDXMKTG_COOKIE_NAME, 'true', max_age=max_age,
        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
        path='/', secure=None, httponly=None,
    )

    return response


def is_logged_in_cookie_set(request):
    """Check whether the request has the logged in cookie set. """
    return settings.EDXMKTG_COOKIE_NAME in request.COOKIES
