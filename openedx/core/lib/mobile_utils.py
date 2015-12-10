"""
Common utilities related to the mobile apps.
"""

import re
from django.conf import settings


def is_request_from_mobile_app(request):
    """
    Returns whether the given request was made by an open edX mobile app,
    either natively or through the mobile web view.

    Note: The check for the user agent works only for mobile apps version 2.1
    and higher.  Previous apps did not update their user agents to include the
    distinguishing string.

    The check for the web view is a temporary check that works for mobile apps
    version 2.0 and higher.  See is_request_from_mobile_web_view for more
    information.

    Args:
        request (HttpRequest)
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return (
        (
            getattr(settings, 'MOBILE_APP_USER_AGENT_ID', None) and
            settings.MOBILE_APP_USER_AGENT_ID.lower() in user_agent
        ) or
        is_request_from_mobile_web_view(request)
    )


PATHS_ACCESSED_BY_MOBILE_WITH_SESSION_COOKIES = [
    r'^/xblock/{usage_key_string}$'.format(usage_key_string=settings.USAGE_KEY_PATTERN),
]


def is_request_from_mobile_web_view(request):
    """
    Returns whether the given request was made by an open edX mobile web
    view using a session cookie.

    Args:
        request (HttpRequest)
    """

    # TODO (MA-1825): This is a TEMPORARY HACK until all of the version 2.0
    # iOS mobile apps have updated.  The earlier versions didn't update their
    # user agents so we are checking for the specific URLs that are
    # accessed through the mobile web view.
    for mobile_path in PATHS_ACCESSED_BY_MOBILE_WITH_SESSION_COOKIES:
        if re.match(mobile_path, request.path):
            return True

    return False
