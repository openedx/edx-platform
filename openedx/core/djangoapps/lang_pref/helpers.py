"""
Language preference cookie helper functions
"""
from django.conf import settings

from openedx.core.djangoapps.lang_pref import COOKIE_DURATION


def get_language_cookie(request, default=None):
    """
    Return the language cookie stored in the request object.
    """
    return request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, default)


def set_language_cookie(request, response, value):
    """
    Set the language cookie in the response object.
    """
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        value=value,
        domain=settings.SHARED_COOKIE_DOMAIN,
        max_age=COOKIE_DURATION,
        secure=request.is_secure(),
        samesite="None" if request.is_secure() else "Lax",
    )


def unset_language_cookie(response):
    """
    Remove the language cookie from the response object.
    """
    response.delete_cookie(
        settings.LANGUAGE_COOKIE_NAME, domain=settings.SHARED_COOKIE_DOMAIN
    )
