"""
Useful helper methods related to the XBlock runtime
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import hashlib
import hmac
import math
import time

from django.conf import settings
from six import text_type


def get_secure_token_for_xblock_handler(user_id, block_key_str, time_idx=0):
    """
    Get a secure token (one-way hash) used to authenticate XBlock handler
    requests. This token replaces both the session ID cookie (or OAuth
    bearer token) and the CSRF token for such requests.

    The token is specific to one user and one XBlock usage ID, though may
    be used for any handler. It expires and is only valid for 2-4 days (our
    current best guess at a reasonable trade off between "what if the user left
    their browser open overnight and tried to continue the next day" which
    should work vs. "for security, tokens should not last too long")

    We use this token because XBlocks may sometimes be sandboxed (run in a
    client-side JavaScript environment with no access to cookies) and
    because the XBlock python and JavaScript handler_url APIs do not provide
    any way of authenticating the handler requests, other than assuming
    cookies are present or including this sort of secure token in the
    handler URL.

    For security, we need these tokens to have an expiration date. So: the
    hash incorporates the current time, rounded to the lowest TOKEN_PERIOD
    value. When checking this, you should check both time_idx=0 and
    time_idx=-1 in case we just recently moved from one time period to
    another (i.e. at the stroke of midnight UTC or similar). The effect of
    this is that each token is valid for 2-4 days.

    (Alternatively, we could make each token expire after exactly X days, but
    that requires storing the expiration date of each token on the server side,
    making the implementation needlessly complex. The "time window" approach we
    are using here also has the advantage that throughout a typical day, the
    token each user gets for a given XBlock doesn't change, which makes
    debugging and reasoning about the system simpler.)
    """
    TOKEN_PERIOD = 24 * 60 * 60 * 2  # These URLs are valid for 2-4 days
    time_token = math.floor(time.time() / TOKEN_PERIOD)
    time_token += TOKEN_PERIOD * time_idx
    check_string = text_type(time_token) + ':' + text_type(user_id) + ':' + block_key_str
    secure_key = hmac.new(settings.SECRET_KEY.encode('utf-8'), check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return secure_key[:20]


def validate_secure_token_for_xblock_handler(user_id, block_key_str, token):
    """
    Returns True if the specified handler authentication token is valid for the
    given XBlock ID and user ID. Otherwise returns false.

    See get_secure_token_for_xblock_handler
    """
    token = token.encode('utf-8')  # This line isn't needed after python 3, nor the .encode('utf-8') below
    token_expected = get_secure_token_for_xblock_handler(user_id, block_key_str).encode('utf-8')
    prev_token_expected = get_secure_token_for_xblock_handler(user_id, block_key_str, -1).encode('utf-8')
    result1 = hmac.compare_digest(token, token_expected)
    result2 = hmac.compare_digest(token, prev_token_expected)
    # All computations happen above this line so this function always takes a
    # constant time to produce its answer (security best practice).
    return bool(result1 or result2)
