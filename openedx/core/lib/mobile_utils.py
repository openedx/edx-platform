"""
Common utilities related to the mobile apps.
"""


import re

from django.conf import settings


def is_request_from_mobile_app(request):
    """
<<<<<<< HEAD
    Returns whether the given request was made by an open edX mobile app,
=======
    Returns whether the given request was made by an Open edX mobile app,
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    either natively or through the mobile web view.

    Args:
        request (HttpRequest)
    """
    if getattr(settings, 'MOBILE_APP_USER_AGENT_REGEXES', None):
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent:
            for user_agent_regex in settings.MOBILE_APP_USER_AGENT_REGEXES:
                if re.search(user_agent_regex, user_agent):
                    return True

    return False
