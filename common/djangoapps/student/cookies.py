"""
Utility functions for setting "logged in" cookies used by subdomains.
"""
from __future__ import unicode_literals

import json
import time

import six
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.dispatch import Signal
from django.utils.http import cookie_date

from student.models import CourseEnrollment

CREATE_LOGON_COOKIE = Signal(providing_args=['user', 'response'])


def _get_cookie_settings(request):
    """ Returns the common cookie settings (e.g. expiration time). """

    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
        expires_time = time.time() + max_age
        expires = cookie_date(expires_time)

    cookie_settings = {
        'max_age': max_age,
        'expires': expires,
        'domain': settings.SESSION_COOKIE_DOMAIN,
        'path': '/',
        'httponly': None,
    }

    return cookie_settings


def set_logged_in_cookies(request, response, user):
    """
    Set cookies indicating that the user is logged in.

    Some installations have an external marketing site configured
    that displays a different UI when the user is logged in
    (e.g. a link to the student dashboard instead of to the login page)

    Currently, two cookies are set:

    * EDXMKTG_LOGGED_IN_COOKIE_NAME: Set to 'true' if the user is logged in.
    * EDXMKTG_USER_INFO_COOKIE_VERSION: JSON-encoded dictionary with user information (see below).

    The user info cookie has the following format:
    {
        "version": 1,
        "username": "test-user",
        "header_urls": {
            "account_settings": "https://example.com/account/settings",
            "learner_profile": "https://example.com/u/test-user",
            "logout": "https://example.com/logout"
        }
    }

    Arguments:
        request (HttpRequest): The request to the view, used to calculate
            the cookie's expiration date based on the session expiration date.
        response (HttpResponse): The response on which the cookie will be set.
        user (User): The currently logged in user.

    Returns:
        HttpResponse

    """
    cookie_settings = _get_cookie_settings(request)

    # Backwards compatibility: set the cookie indicating that the user
    # is logged in.  This is just a boolean value, so it's not very useful.
    # In the future, we should be able to replace this with the "user info"
    # cookie set below.
    response.set_cookie(
        settings.EDXMKTG_LOGGED_IN_COOKIE_NAME.encode('utf-8'),
        'true',
        secure=None,
        **cookie_settings
    )

    set_user_info_cookie(response, request)

    # give signal receivers a chance to add cookies
    CREATE_LOGON_COOKIE.send(sender=None, user=user, response=response)

    return response


def set_user_info_cookie(response, request):
    """ Sets the user info cookie on the response. """
    cookie_settings = _get_cookie_settings(request)

    # In production, TLS should be enabled so that this cookie is encrypted
    # when we send it.  We also need to set "secure" to True so that the browser
    # will transmit it only over secure connections.
    #
    # In non-production environments (acceptance tests, devstack, and sandboxes),
    # we still want to set this cookie.  However, we do NOT want to set it to "secure"
    # because the browser won't send it back to us.  This can cause an infinite redirect
    # loop in the third-party auth flow, which calls `is_logged_in_cookie_set` to determine
    # whether it needs to set the cookie or continue to the next pipeline stage.
    user_info_cookie_is_secure = request.is_secure()
    user_info = get_user_info_cookie_data(request)

    response.set_cookie(
        settings.EDXMKTG_USER_INFO_COOKIE_NAME.encode('utf-8'),
        json.dumps(user_info),
        secure=user_info_cookie_is_secure,
        **cookie_settings
    )


def get_user_info_cookie_data(request):
    """ Returns information that wil populate the user info cookie. """
    user = request.user

    # Set a cookie with user info.  This can be used by external sites
    # to customize content based on user information.  Currently,
    # we include information that's used to customize the "account"
    # links in the header of subdomain sites (such as the marketing site).
    header_urls = {'logout': reverse('logout')}

    # Unfortunately, this app is currently used by both the LMS and Studio login pages.
    # If we're in Studio, we won't be able to reverse the account/profile URLs.
    # To handle this, we don't add the URLs if we can't reverse them.
    # External sites will need to have fallback mechanisms to handle this case
    # (most likely just hiding the links).
    try:
        header_urls['account_settings'] = reverse('account_settings')
        header_urls['learner_profile'] = reverse('learner_profile', kwargs={'username': user.username})
    except NoReverseMatch:
        pass

    # Convert relative URL paths to absolute URIs
    for url_name, url_path in six.iteritems(header_urls):
        header_urls[url_name] = request.build_absolute_uri(url_path)

    user_info = {
        'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
        'username': user.username,
        'header_urls': header_urls,
        'enrollmentStatusHash': CourseEnrollment.generate_enrollment_status_hash(user)
    }

    return user_info


def delete_logged_in_cookies(response):
    """
    Delete cookies indicating that the user is logged in.

    Arguments:
        response (HttpResponse): The response sent to the client.

    Returns:
        HttpResponse

    """
    for cookie_name in [settings.EDXMKTG_LOGGED_IN_COOKIE_NAME, settings.EDXMKTG_USER_INFO_COOKIE_NAME]:
        response.delete_cookie(
            cookie_name.encode('utf-8'),
            path='/',
            domain=settings.SESSION_COOKIE_DOMAIN
        )

    return response


def is_logged_in_cookie_set(request):
    """Check whether the request has logged in cookies set. """
    return (
        settings.EDXMKTG_LOGGED_IN_COOKIE_NAME in request.COOKIES and
        settings.EDXMKTG_USER_INFO_COOKIE_NAME in request.COOKIES
    )
