"""
Useful helper methods related to the XBlock runtime
"""

import hashlib
import hmac
import math
import time
from uuid import uuid4

import crum
from django.conf import settings


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
    # Impact of exposure of the SECRET_KEY or XBLOCK_HANDLER_TOKEN_KEYS:
    # An actor with the key could produce valid secure tokens for any given user_id and xblock and
    # could submit answers to questions on behalf of other users. This would violate the integrity
    # of the answer data on our platform.
    # Estimated CVSS Base Score: 7.5
    # Score URL: https://www.first.org/cvss/calculator/3.1#CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N
    # Environment score not given because the importance of the environment may change over time.

    # If this key is actually exposed to malicious actors, we should do a rapid rotation that
    # breaks people because in this case a malicious actor can generate valid tokens to submit
    # answers as any user.

    # XBLOCK_HANDLER_TOKEN_KEYS takes the form of a list of strings with at least 128 bits of entropy each.
    # It is reasonable to use django.core.management.utils.get_random_secret_key to generate these keys.

    # Transitioning from SECRET_KEY to XBLOCK_HANDLER_TOKEN_KEYS:
    #
    # 1. Add a new xblock handler specific secret key and the current secret key to the
    # XBLOCK_HANDLER_TOKEN_KEYS list in your LMS and Studio settings file or yaml. The order of the keys
    # matters and so the new xblock specific key should be at index 0.
    #   eg. XBLOCK_HANDLER_TOKEN_KEYS = ["<new xblock specific hashing key>", "<value of django secret key>"]
    # 2. Wait 4 days after the code has been deployed to production.
    # 3. Remove the django secret key from the XBLOCK_HANDLER_TOKEN_KEYS list.
    #   eg. XBLOCK_HANDLER_TOKEN_KEYS = ["<new xblock specific hashing key>"]

    # Rotation Process (Assumes you've already transitioned from SECRET_KEY to XBLOCK_HANDLER_TOKEN_KEYS):
    #
    # If the likelihood that the old key has been exposed to malicious actors is high, you should do a rapid rotation
    # that breaks people because in this case a malicious actor can generate valid tokens to submit answers
    # impersonating any user.  If the likelihood of a malicious actor is high, skip step 2 from this process (Start
    # using only the new key right away.)
    # 1. Add the newly generated hashing key at index 0 of the XBLOCK_HANDLER_TOKEN_KEYS list in your settings.
    #   eg. XBLOCK_HANDLER_TOKEN_KEYS = ["<new xblock specific hashing key>", "<old xblock specific hashing key>"]
    # 2. Wait 4 days after the code has been deployed to production.
    # 3. Remove the old key from the list.
    #   eg. XBLOCK_HANDLER_TOKEN_KEYS = ["<new xblock specific hashing key>"]

    # Fall back to SECRET_KEY if XBLOCK_HANDLER_TOKEN_KEYS is not set or is an empty list.
    if getattr(settings, "XBLOCK_HANDLER_TOKEN_KEYS", None):
        hashing_key = settings.XBLOCK_HANDLER_TOKEN_KEYS[0]
    else:
        hashing_key = settings.SECRET_KEY

    return _get_secure_token_for_xblock_handler(user_id, block_key_str, time_idx, hashing_key)


def _get_secure_token_for_xblock_handler(user_id, block_key_str, time_idx: int, hashing_key: str):
    """
    Internal function to extract repeating hashing steps which we
    call multiple times with different time_idx and hashing key.
    """
    TOKEN_PERIOD = 24 * 60 * 60 * 2  # These URLs are valid for 2-4 days
    # time_token is the number of time periods since unix epoch
    time_token = math.floor(time.time() / TOKEN_PERIOD)
    time_token += time_idx
    check_string = str(time_token) + ':' + str(user_id) + ':' + block_key_str
    secure_key = hmac.new(hashing_key.encode('utf-8'), check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return secure_key[:20]


def validate_secure_token_for_xblock_handler(user_id, block_key_str, token):
    """
    Returns True if the specified handler authentication token is valid for the
    given Xblock ID and user ID. Otherwise returns false.

    See get_secure_token_for_xblock_handler
    """
    if getattr(settings, "XBLOCK_HANDLER_TOKEN_KEYS", None):
        hashing_keys = settings.XBLOCK_HANDLER_TOKEN_KEYS
    else:
        hashing_keys = [settings.SECRET_KEY]

    final_result = False
    for key in hashing_keys:
        final_result |= _validate_secure_token_for_xblock_handler(user_id, block_key_str, token, key)

    # We check all keys so that the computation takes a constant amount of
    # time to produce its answer (security best practice).
    return final_result


def _validate_secure_token_for_xblock_handler(user_id, block_key_str, token: str, hashing_key):
    """
    Internal function to validate the incoming token with tokens generated with the given
    hashing key.
    """
    token_expected = _get_secure_token_for_xblock_handler(user_id, block_key_str, 0, hashing_key)
    prev_token_expected = _get_secure_token_for_xblock_handler(user_id, block_key_str, -1, hashing_key)
    result1 = hmac.compare_digest(token, token_expected)
    result2 = hmac.compare_digest(token, prev_token_expected)
    # All computations happen above this line so this function always takes a
    # constant time to produce its answer (security best practice).
    return bool(result1 or result2)


def get_xblock_id_for_anonymous_user(user):
    """
    Get a unique string that identifies the current anonymous (not logged in)
    user. (This is different than the "anonymous user ID", which is an
    anonymized identifier for a logged in user.)

    Note that this ID is a string, not an int. It is guaranteed to be in a
    unique namespace that won't collide with "normal" user IDs, even when
    they are converted to a string.
    """
    if not user or not user.is_anonymous:
        raise TypeError("get_xblock_id_for_anonymous_user() is only for anonymous (not logged in) users.")
    if hasattr(user, 'xblock_id_for_anonymous_user'):
        # If code elsewhere (like the xblock_handler API endpoint) has stored
        # the key on the AnonymousUser object, just return that - it supersedes
        # everything else:
        return user.xblock_id_for_anonymous_user
    # We use the session to track (and create if needed) a unique ID for this anonymous user:
    current_request = crum.get_current_request()
    if current_request and current_request.session:
        # Make sure we have a key for this user:
        if "xblock_id_for_anonymous_user" not in current_request.session:
            new_id = f"anon{uuid4().hex[:20]}"
            current_request.session["xblock_id_for_anonymous_user"] = new_id
        return current_request.session["xblock_id_for_anonymous_user"]
    else:
        raise RuntimeError("Cannot get a user ID for an anonymous user outside of an HTTP request context.")
