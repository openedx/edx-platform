"""
This module defines SafeSessionMiddleware that makes use of a
SafeCookieData that cryptographically binds the user to the session id
in the cookie.

The implementation is inspired by the proposal in the following paper:
http://www.cse.msu.edu/~alexliu/publications/Cookie/cookie.pdf

Note: The proposed protocol protects against replay attacks by
incorporating the session key used in the SSL connection.  However,
this does not suit our needs since we want the ability to reuse the
same cookie over multiple SSL connections.  So instead, we mitigate
replay attacks by enforcing session cookie expiration
(via TimestampSigner) and assuming SESSION_COOKIE_SECURE (see below).

We use django's built-in Signer class, which makes use of a built-in
salted_hmac function that derives a usage-specific key from the
server's SECRET_KEY, as proposed in the paper.

Note: The paper proposes deriving a usage-specific key from the
session's expiration time in order to protect against volume attacks.
However, since django does not always use an expiration time, we
instead use a random key salt to prevent volume attacks.

In fact, we actually use a specialized subclass of Signer called
TimestampSigner. This signer binds a timestamp along with the signed
data and verifies that the signature has not expired.  We do this
since django's session stores do not actually verify the expiration
of the session cookies.  Django instead relies on the browser to honor
session cookie expiration.

The resulting safe cookie data that gets stored as the value in the
session cookie is a tuple of:
    (
        version,
        session_id,
        key_salt,
        signature
    )

    where signature is:
        signed_data : base64(HMAC_SHA1(signed_data, usage_key))

    where signed_data is:
        H(version | session_id | user_id) : timestamp

    where usage_key is:
        SHA1(key_salt + 'signer' + settings.SECRET_KEY)

Note: We assume that the SESSION_COOKIE_SECURE setting is set to
TRUE to prevent inadvertent leakage of the session cookie to a
person-in-the-middle.  The SESSION_COOKIE_SECURE flag indicates
to the browser that the cookie should be sent only over an
SSL-protected channel.  Otherwise, a session hijacker could copy
the entire cookie and use it to impersonate the victim.

"""


from base64 import b64encode
from contextlib import contextmanager
from hashlib import sha256
from logging import ERROR, getLogger

import six
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.views import redirect_to_login
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import python_2_unicode_compatible

from six import text_type  # pylint: disable=ungrouped-imports

from openedx.core.lib.mobile_utils import is_request_from_mobile_app

log = getLogger(__name__)


class SafeCookieError(Exception):
    """
    An exception class for safe cookie related errors.
    """
    def __init__(self, error_message):
        super(SafeCookieError, self).__init__(error_message)
        log.error(error_message)


@python_2_unicode_compatible
class SafeCookieData(object):
    """
    Cookie data that cryptographically binds and timestamps the user
    to the session id.  It verifies the freshness of the cookie by
    checking its creation date using settings.SESSION_COOKIE_AGE.
    """
    CURRENT_VERSION = '1'
    SEPARATOR = u"|"

    def __init__(self, version, session_id, key_salt, signature):
        """
        Arguments:
            version (string): The data model version of the safe cookie
                data that is checked for forward and backward
                compatibility.
            session_id (string): Unique and unguessable session
                identifier to which this safe cookie data is bound.
            key_salt (string): A securely generated random string that
                is used to derive a usage-specific secret key for
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
            key_salt=get_random_string(),
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
            raw_cookie_components = six.text_type(safe_cookie_string).split(cls.SEPARATOR)
            safe_cookie_data = SafeCookieData(*raw_cookie_components)
        except TypeError:
            raise SafeCookieError(
                u"SafeCookieData BWC parse error: {0!r}.".format(safe_cookie_string)
            )
        else:
            if safe_cookie_data.version != cls.CURRENT_VERSION:
                raise SafeCookieError(
                    u"SafeCookieData version {0!r} is not supported. Current version is {1}.".format(
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
        Computes the signature of this safe cookie data.
        A signed value of hash(version | session_id | user_id):timestamp
        with a usage-specific key derived from key_salt.
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
            log.error(u"SafeCookieData '%r' is not bound to user '%s'.", six.text_type(self), user_id)
        except signing.BadSignature as sig_error:
            log.error(
                u"SafeCookieData signature error for cookie data {0!r}: {1}".format(  # pylint: disable=logging-format-interpolation
                    six.text_type(self),
                    text_type(sig_error),
                )
            )
        return False

    def _compute_digest(self, user_id):
        """
        Returns hash(version | session_id | user_id |)
        """
        hash_func = sha256()
        for data_item in [self.version, self.session_id, user_id]:
            hash_func.update(six.b(six.text_type(data_item)))
            hash_func.update(six.b('|'))
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
        if not session_id or session_id == six.text_type(None):
            # The session ID should always be valid in the cookie.
            raise SafeCookieError(
                u"SafeCookieData not created due to invalid value for session_id '{}' for user_id '{}'.".format(
                    session_id,
                    user_id,
                ))

        if not user_id:
            # The user ID is sometimes not set for
            # 3rd party Auth and external Auth transactions
            # as some of the session requests are made as
            # Anonymous users.
            log.debug(
                u"SafeCookieData received empty user_id '%s' for session_id '%s'.",
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

        process_request_response = super(SafeSessionMiddleware, self).process_request(request)  # Step 3
        if process_request_response:
            # The process_request pipeline has been short circuited so
            # return the response.
            return process_request_response

        if cookie_data_string and request.session.get(SESSION_KEY):

            user_id = self.get_user_id_from_session(request)
            if safe_cookie_data.verify(user_id):  # Step 4
                request.safe_cookie_verified_user_id = user_id  # Step 5
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
        response = super(SafeSessionMiddleware, self).process_response(request, response)  # Step 1

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
            if request.safe_cookie_verified_user_id != request.user.id:
                # The user at response time is expected to be None when the user
                # is logging out. To prevent extra noise in the logs,
                # conditionally set the log level.
                log_func = log.debug if request.user.id is None else log.warning
                log_func(
                    u"SafeCookieData user at request '{0}' does not match user at response: '{1}'".format(
                        request.safe_cookie_verified_user_id,
                        request.user.id,
                    ),
                )
            if request.safe_cookie_verified_user_id != userid_in_session:
                log.warning(
                    u"SafeCookieData user at request '{0}' does not match user in session: '{1}'".format(  # pylint: disable=logging-format-interpolation
                        request.safe_cookie_verified_user_id,
                        userid_in_session,
                    ),
                )

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
        cookies[settings.SESSION_COOKIE_NAME] = six.text_type(safe_cookie_data)


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
        u"Malformed Cookie Header? First 4K, in Base64: %s",
        b64encode(six.b(cookie_header))
    )

    # Note, there is no request.user attribute at this point.
    if hasattr(request, 'session') and hasattr(request.session, 'session_key'):
        log.warning(
            u"SafeCookieData deleted session cookie for session %s",
            request.session.session_key
        )


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
