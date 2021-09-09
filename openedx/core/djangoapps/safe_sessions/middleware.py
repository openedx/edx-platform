"""
This module defines SafeSessionMiddleware that makes use of a
SafeCookieData that cryptographically binds the user to the session id
in the cookie.

The implementation is inspired in part by the proposal in the paper
<http://www.cse.msu.edu/~alexliu/publications/Cookie/cookie.pdf>
but deviates in a number of ways; mostly it just uses the technique
of an intermediate key for HMAC.

Note: The proposed protocol protects against replay attacks by
use of channel binding—specifically, by
incorporating the session key used in the SSL connection.  However,
this does not suit our needs since we want the ability to reuse the
same cookie over multiple browser sessions, and in any case the server
will be behind a load balancer and won't have access to the correct
SSL session information.  So instead, we mitigate
replay attacks by enforcing session cookie expiration
(via TimestampSigner) and assuming SESSION_COOKIE_SECURE (see below).

We use django's built-in Signer class, which makes use of a built-in
salted_hmac function that derives an intermediate key from the
server's SECRET_KEY, as proposed in the paper.

Note: The paper proposes deriving an intermediate key from the
session's expiration time in order to protect against volume attacks.
(Note that these hypothetical attacks would only succeed if HMAC-SHA1
were found to be weak, and there is presently no indication of this.)
However, since django does not always use an expiration time, we
instead use a random key salt to prevent volume attacks.

In fact, we actually use a specialized subclass of Signer called
TimestampSigner. This signer binds a timestamp along with the signed
data and verifies that the signature has not expired.  We do this
since django's session stores do not actually verify the expiration
of the session cookies.  Django instead relies on the browser to honor
session cookie expiration.

The resulting safe cookie data that gets stored as the value in the
session cookie is:

    version '|' session_id '|' key_salt '|' signed_hash

where signed_hash is a structure incorporating the following value and
a MAC (via TimestampSigner):

    SHA256(version '|' session_id '|' user_id '|')

TimestampSigner uses HMAC-SHA1 to derive a key from key_salt and the
server's SECRET_KEY; see django.core.signing for more details on the
structure of the output (which takes the form of colon-delimited
Base64.)

Note: We assume that the SESSION_COOKIE_SECURE setting is set to
TRUE to prevent inadvertent leakage of the session cookie to a
person-in-the-middle.  The SESSION_COOKIE_SECURE flag indicates
to the browser that the cookie should be sent only over an
SSL-protected channel.  Otherwise, a connection eavesdropper could copy
the entire cookie and use it to impersonate the victim.

Custom Attributes:
    safe_sessions.user_mismatch: 'request-response-mismatch' | 'request-session-mismatch'
        This attribute can be one of the above two values which correspond to the kind of comparison
        that failed when processing the response. See SafeSessionMiddleware._verify_user
"""

import inspect
from base64 import b64encode
from contextlib import contextmanager
from hashlib import sha256
from logging import ERROR, getLogger

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.views import redirect_to_login
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.utils.deprecation import MiddlewareMixin

from edx_django_utils.monitoring import set_custom_attribute

from openedx.core.lib.mobile_utils import is_request_from_mobile_app

# .. toggle_name: LOG_REQUEST_USER_CHANGES
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: Turn this toggle on to log anytime the `user` attribute of the request object gets
#   changed.  This will also log the location where the change is coming from to quickly find issues.
# .. toggle_warnings: This logging will be very verbose and so should probably not be left on all the time.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2021-03-25
# .. toggle_tickets: https://openedx.atlassian.net/browse/ARCHBOM-1718
LOG_REQUEST_USER_CHANGES = getattr(settings, 'LOG_REQUEST_USER_CHANGES', False)

log = getLogger(__name__)


class SafeCookieError(Exception):
    """
    An exception class for safe cookie related errors.
    """
    def __init__(self, error_message):
        super().__init__(error_message)
        log.error(error_message)


class SafeCookieData:
    """
    Cookie data that cryptographically binds and timestamps the user
    to the session id.  It verifies the freshness of the cookie by
    checking its creation date using settings.SESSION_COOKIE_AGE.
    """
    CURRENT_VERSION = '1'
    SEPARATOR = "|"

    def __init__(self, version, session_id, key_salt, signature):
        """
        Arguments:
            version (string): The data model version of the safe cookie
                data that is checked for forward and backward
                compatibility.
            session_id (string): Unique and unguessable session
                identifier to which this safe cookie data is bound.
            key_salt (string): A securely generated random string that
                is used to derive an intermediate secret key for
                signing the safe cookie data to protect against volume
                attacks.
            signature (string): Cryptographically created signature
                for the safe cookie data that binds the session_id
                and its corresponding user as described at the top of
                this file.
        """
        self.version = version
        self.session_id = session_id
        self.key_salt = key_salt
        self.signature = signature

    @classmethod
    def create(cls, session_id, user_id):
        """
        Factory method for creating the cryptographically bound
        safe cookie data for the session and the user.

        Raises SafeCookieError if session_id is None.
        """
        cls._validate_cookie_params(session_id, user_id)
        safe_cookie_data = SafeCookieData(
            cls.CURRENT_VERSION,
            session_id,
            key_salt=get_random_string(length=12),
            signature=None,
        )
        safe_cookie_data.sign(user_id)
        return safe_cookie_data

    @classmethod
    def parse(cls, safe_cookie_string):
        """
        Factory method that parses the serialized safe cookie data,
        verifies the version, and returns the safe cookie object.

        Raises SafeCookieError if there are any issues parsing the
        safe_cookie_string.
        """
        try:
            raw_cookie_components = str(safe_cookie_string).split(cls.SEPARATOR)
            safe_cookie_data = SafeCookieData(*raw_cookie_components)
        except TypeError:
            raise SafeCookieError(  # lint-amnesty, pylint: disable=raise-missing-from
                f"SafeCookieData BWC parse error: {safe_cookie_string!r}."
            )
        else:
            if safe_cookie_data.version != cls.CURRENT_VERSION:
                raise SafeCookieError(
                    "SafeCookieData version {!r} is not supported. Current version is {}.".format(
                        safe_cookie_data.version,
                        cls.CURRENT_VERSION,
                    ))
            return safe_cookie_data

    def __str__(self):
        """
        Returns a string serialization of the safe cookie data.
        """
        return self.SEPARATOR.join([self.version, self.session_id, self.key_salt, self.signature])

    def sign(self, user_id):
        """
        Signs the safe cookie data for this user using a timestamped signature
        and an intermediate key derived from key_salt and server's SECRET_KEY.
        Value under signature is the hexadecimal string from
        SHA256(version '|' session_id '|' user_id '|').
        """
        data_to_sign = self._compute_digest(user_id)
        self.signature = signing.dumps(data_to_sign, salt=self.key_salt)

    def verify(self, user_id):
        """
        Verifies the signature of this safe cookie data.
        Successful verification implies this cookie data is fresh
        (not expired) and bound to the given user.
        """
        try:
            unsigned_data = signing.loads(self.signature, salt=self.key_salt, max_age=settings.SESSION_COOKIE_AGE)
            if unsigned_data == self._compute_digest(user_id):
                return True
            log.error("SafeCookieData '%r' is not bound to user '%s'.", str(self), user_id)
        except signing.BadSignature as sig_error:
            log.error(
                "SafeCookieData signature error for cookie data {!r}: {}".format(  # pylint: disable=logging-format-interpolation
                    str(self),
                    str(sig_error),
                )
            )
        return False

    def _compute_digest(self, user_id):
        """
        Returns SHA256(version '|' session_id '|' user_id '|') hex string.
        """
        hash_func = sha256()
        for data_item in [self.version, self.session_id, user_id]:
            hash_func.update(str(data_item).encode())
            hash_func.update(b'|')
        return hash_func.hexdigest()

    @staticmethod
    def _validate_cookie_params(session_id, user_id):
        """
        Validates the given parameters for cookie creation.

        Raises SafeCookieError if session_id is None.
        """
        # Compare against unicode(None) as well since the 'value'
        # property of a cookie automatically serializes None to a
        # string.
        if not session_id or session_id == str(None):
            # The session ID should always be valid in the cookie.
            raise SafeCookieError(
                "SafeCookieData not created due to invalid value for session_id '{}' for user_id '{}'.".format(
                    session_id,
                    user_id,
                ))

        if not user_id:
            # The user ID is sometimes not set for
            # 3rd party Auth and external Auth transactions
            # as some of the session requests are made as
            # Anonymous users.
            log.debug(
                "SafeCookieData received empty user_id '%s' for session_id '%s'.",
                user_id,
                session_id,
            )


class SafeSessionMiddleware(SessionMiddleware, MiddlewareMixin):
    """
    A safer middleware implementation that uses SafeCookieData instead
    of just the session id to lookup and verify a user's session.
    """
    def process_request(self, request):
        """
        Processing the request is a multi-step process, as follows:

        Step 1. The safe_cookie_data is parsed and verified from the
        session cookie.

        Step 2. The session_id is retrieved from the safe_cookie_data
        and stored in place of the session cookie value, to be used by
        Django's Session middleware.

        Step 3. Call Django's Session Middleware to find the session
        corresponding to the session_id and to set the session in the
        request.

        Step 4. Once the session is retrieved, verify that the user
        bound in the safe_cookie_data matches the user attached to the
        server's session information.

        Step 5. If all is successful, the now verified user_id is stored
        separately in the request object so it is available for another
        final verification before sending the response (in
        process_response).
        """
        cookie_data_string = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        if cookie_data_string:

            try:
                safe_cookie_data = SafeCookieData.parse(cookie_data_string)  # Step 1

            except SafeCookieError:
                # For security reasons, we don't support requests with
                # older or invalid session cookie models.
                return self._on_user_authentication_failed(request)

            else:
                request.COOKIES[settings.SESSION_COOKIE_NAME] = safe_cookie_data.session_id  # Step 2

        process_request_response = super().process_request(request)  # Step 3  # lint-amnesty, pylint: disable=assignment-from-no-return, super-with-arguments
        if process_request_response:
            # The process_request pipeline has been short circuited so
            # return the response.
            return process_request_response

        if cookie_data_string and request.session.get(SESSION_KEY):

            user_id = self.get_user_id_from_session(request)
            if safe_cookie_data.verify(user_id):  # Step 4
                request.safe_cookie_verified_user_id = user_id  # Step 5
                if LOG_REQUEST_USER_CHANGES:
                    log_request_user_changes(request)
            else:
                return self._on_user_authentication_failed(request)

    def process_response(self, request, response):
        """
        When creating a cookie for the response, a safe_cookie_data
        is created and put in place of the session_id in the session
        cookie.

        Also, the session cookie is deleted if prior verification failed
        or the designated user in the request has changed since the
        original request.

        Processing the response is a multi-step process, as follows:

        Step 1. Call the parent's method to generate the basic cookie.

        Step 2. Verify that the user marked at the time of
        process_request matches the user at this time when processing
        the response.  If not, log the error.

        Step 3. If a cookie is being sent with the response, update
        the cookie by replacing its session_id with a safe_cookie_data
        that binds the session and its corresponding user.

        Step 4. Delete the cookie, if it's marked for deletion.

        """
        response = super().process_response(request, response)  # Step 1

        if not _is_cookie_marked_for_deletion(request) and _is_cookie_present(response):
            try:
                user_id_in_session = self.get_user_id_from_session(request)
                with controlled_logging(request, log):
                    self._verify_user(request, user_id_in_session)  # Step 2

                    # Use the user_id marked in the session instead of the
                    # one in the request in case the user is not set in the
                    # request, for example during Anonymous API access.
                    self.update_with_safe_session_cookie(response.cookies, user_id_in_session)  # Step 3

            except SafeCookieError:
                _mark_cookie_for_deletion(request)

        if _is_cookie_marked_for_deletion(request):
            _delete_cookie(request, response)  # Step 4

        return response

    @staticmethod
    def _on_user_authentication_failed(request):
        """
        To be called when user authentication fails when processing
        requests in the middleware. Sets a flag to delete the user's
        cookie and redirects the user to the login page.
        """
        _mark_cookie_for_deletion(request)

        # Mobile apps have custom handling of authentication failures. They
        # should *not* be redirected to the website's login page.
        if is_request_from_mobile_app(request):
            return HttpResponse(status=401)

        return redirect_to_login(request.path)

    @staticmethod
    def _verify_user(request, userid_in_session):
        """
        Logs an error if the user marked at the time of process_request
        does not match either the current user in the request or the
        given userid_in_session.
        """
        if hasattr(request, 'safe_cookie_verified_user_id'):
            if hasattr(request.user, 'real_user'):
                # If a view overrode the request.user with a masqueraded user, this will
                #   revert/clean-up that change during response processing.
                request.user = request.user.real_user
            # The user at response time is expected to be None when the user
            # is logging out.  We won't log that.
            if request.safe_cookie_verified_user_id != request.user.id and request.user.id is not None:
                log.warning(
                    (
                        "SafeCookieData user at request '{}' does not match user at response: '{}' "
                        "for request path '{}'"
                    ).format(  # pylint: disable=logging-format-interpolation
                        request.safe_cookie_verified_user_id, request.user.id, request.path,
                    ),
                )
                set_custom_attribute("safe_sessions.user_mismatch", "request-response-mismatch")
            # The user session at response time is expected to be None when the user
            # is logging out.  We won't log that.
            if request.safe_cookie_verified_user_id != userid_in_session and userid_in_session is not None:
                log.warning(
                    (
                        "SafeCookieData user at request '{}' does not match user in session: '{}' "
                        "for request path '{}'"
                    ).format(  # pylint: disable=logging-format-interpolation
                        request.safe_cookie_verified_user_id, userid_in_session, request.path,
                    ),
                )
                set_custom_attribute("safe_sessions.user_mismatch", "request-session-mismatch")

    @staticmethod
    def get_user_id_from_session(request):
        """
        Return the user_id stored in the session of the request.
        """
        # Starting in django 1.8, the user_id is now serialized
        # as a string in the session.  Before, it was stored
        # directly as an integer. If back-porting to prior to
        # django 1.8, replace the implementation of this method
        # with:
        # return request.session[SESSION_KEY]
        from django.contrib.auth import _get_user_session_key
        try:
            return _get_user_session_key(request)
        except KeyError:
            return None

    @staticmethod
    def set_user_id_in_session(request, user):
        """
        Stores the user_id in the session of the request.
        Used by unit tests.
        """
        # Starting in django 1.8, the user_id is now serialized
        # as a string in the session.  Before, it was stored
        # directly as an integer. If back-porting to prior to
        # django 1.8, replace the implementation of this method
        # with:
        # request.session[SESSION_KEY] = user.id
        request.session[SESSION_KEY] = user._meta.pk.value_to_string(user)

    @staticmethod
    def update_with_safe_session_cookie(cookies, user_id):
        """
        Replaces the session_id in the session cookie with a freshly
        computed safe_cookie_data.
        """
        # Create safe cookie data that binds the user with the session
        # in place of just storing the session_key in the cookie.
        safe_cookie_data = SafeCookieData.create(
            cookies[settings.SESSION_COOKIE_NAME].value,
            user_id,
        )

        # Update the cookie's value with the safe_cookie_data.
        cookies[settings.SESSION_COOKIE_NAME] = str(safe_cookie_data)


def _mark_cookie_for_deletion(request):
    """
    Updates the given request object to designate that the session
    cookie should be deleted.
    """
    request.need_to_delete_cookie = True


def _is_cookie_marked_for_deletion(request):
    """
    Returns whether the session cookie has been designated for deletion
    in the given request object.
    """
    return getattr(request, 'need_to_delete_cookie', False)


def _is_cookie_present(response):
    """
    Returns whether the session cookie is present in the response.
    """
    return (
        response.cookies.get(settings.SESSION_COOKIE_NAME) and  # cookie in response
        response.cookies[settings.SESSION_COOKIE_NAME].value  # cookie is not empty
    )


def _delete_cookie(request, response):
    """
    Delete the cookie by setting the expiration to a date in the past,
    while maintaining the domain, secure, and httponly settings.
    """
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        max_age=0,
        expires='Thu, 01-Jan-1970 00:00:00 GMT',
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
    )

    # Log the cookie, but cap the length and base64 encode to make sure nothing
    # malicious gets directly dumped into the log.
    cookie_header = request.META.get('HTTP_COOKIE', '')[:4096]
    log.warning(
        "Malformed Cookie Header? First 4K, in Base64: %s",
        b64encode(str(cookie_header).encode())
    )

    # Note, there is no request.user attribute at this point.
    if hasattr(request, 'session') and hasattr(request.session, 'session_key'):
        log.warning(
            "SafeCookieData deleted session cookie for session %s",
            request.session.session_key
        )


def log_request_user_changes(request):
    """
    Instrument the request object so that we log changes to the `user` attribute. This is done by
    changing the `__class__` attribute of the request object to point to a new class we created
    on the fly which is exactly the same as the underlying request class but with an override for
    the `__setattr__` function to catch the attribute chages.
    """
    original_user = getattr(request, 'user', None)

    class SafeSessionRequestWrapper(request.__class__):
        """
        A wrapper class for the request object.
        """

        def __setattr__(self, name, value):
            nonlocal original_user
            if name == 'user':
                stack = inspect.stack()
                # Written this way in case you need more of the stack for debugging.
                location = "\n".join("%30s : %s:%d" % (t[3], t[1], t[2]) for t in stack[0:12])

                if not hasattr(request, name):
                    original_user = value
                    if hasattr(value, 'id'):
                        log.info(
                            f"SafeCookieData: Setting for the first time: {value.id!r}\n"
                            f"{location}"
                        )
                    else:
                        log.info(
                            f"SafeCookieData: Setting for the first time, but user has no id: {value!r}\n"
                            f"{location}"
                        )
                elif value != getattr(request, name):
                    current_user = getattr(request, name)
                    if hasattr(value, 'id'):
                        log.info(
                            f"SafeCookieData: Changing request user. "
                            f"Originally {original_user.id!r}, now {current_user.id!r} and will become {value.id!r}\n"
                            f"{location}"
                        )
                    else:
                        log.info(
                            f"SafeCookieData: Changing request user but user has no id. "
                            f"Originally {original_user!r}, now {current_user!r} and will become {value!r}\n"
                            f"{location}"
                        )

                else:
                    # Value being set but not actually changing.
                    pass
            return super().__setattr__(name, value)
    request.__class__ = SafeSessionRequestWrapper


def _is_from_logout(request):
    """
    Returns whether the request has come from logout action to see if
    'is_from_logout' attribute is present.
    """
    return getattr(request, 'is_from_logout', False)


@contextmanager
def controlled_logging(request, logger):
    """
    Control the logging by changing logger's level if
    the request is from logout.
    """
    default_level = None
    from_logout = _is_from_logout(request)
    if from_logout:
        default_level = logger.getEffectiveLevel()
        logger.setLevel(ERROR)

    try:
        yield
    finally:
        if from_logout:
            logger.setLevel(default_level)
