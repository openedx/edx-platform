"""
Code to get ip from request.
"""
from uuid import uuid4

from ipware.ip import get_client_ip


def real_ip(group, request):  # pylint: disable=unused-argument
    return get_client_ip(request)[0]


def request_post_email(group, request) -> str:  # pylint: disable=unused-argument
    """
    Return the the email post param if it exists, otherwise return a
    random id.

    If the request doesn't have an email post body param, treat it as
    a unique key. This will probably mean that it will not get rate limited.

    This ratelimit key function is meant to be used with the user_authn/views/login.py::login_user
    function.  To rate-limit any first party auth.  For 3rd party auth, there is separate rate limiting
    currently in place so we don't do any rate limiting for that case here.
    """

    email = request.POST.get('email')
    if not email:
        email = str(uuid4())

    return email
