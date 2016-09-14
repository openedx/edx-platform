"""
Shared test utilities for Safe Sessions tests
"""

from contextlib import contextmanager
from mock import patch


class TestSafeSessionsLogMixin(object):
    """
    Test Mixin class with helpers for testing log method
    calls in the safe sessions middleware.
    """
    @contextmanager
    def assert_logged(self, log_string, log_level='error'):
        """
        Asserts that the logger was called with the given
        log_level and with a regex of the given string.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.' + log_level) as mock_log:
            yield
            self.assertTrue(mock_log.called)
            self.assertRegexpMatches(mock_log.call_args_list[0][0][0], log_string)

    @contextmanager
    def assert_not_logged(self):
        """
        Asserts that the logger was not called with either a warning
        or an error.
        """
        with self.assert_no_error_logged():
            with self.assert_no_warning_logged():
                yield

    @contextmanager
    def assert_no_warning_logged(self):
        """
        Asserts that the logger was not called with a warning.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.warning') as mock_log:
            yield
            self.assertFalse(mock_log.called)

    @contextmanager
    def assert_no_error_logged(self):
        """
        Asserts that the logger was not called with an error.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.error') as mock_log:
            yield
            self.assertFalse(mock_log.called)

    @contextmanager
    def assert_signature_error_logged(self, sig_error_string):
        """
        Asserts that the logger was called when signature
        verification failed on a SafeCookieData object,
        either because of a parse error or a cryptographic
        failure.

        The sig_error_string is the expected additional
        context logged with the error.
        """
        with self.assert_logged(r'SafeCookieData signature error .*|test_session_id|.*: ' + sig_error_string):
            yield

    @contextmanager
    def assert_incorrect_signature_logged(self):
        """
        Asserts that the logger was called when signature
        verification failed on a SafeCookieData object
        due to a cryptographic failure.
        """
        with self.assert_signature_error_logged('Signature .* does not match'):
            yield

    @contextmanager
    def assert_incorrect_user_logged(self):
        """
        Asserts that the logger was called upon finding that
        the SafeCookieData object is not bound to the expected
        user.
        """
        with self.assert_logged(r'SafeCookieData .* is not bound to user'):
            yield

    @contextmanager
    def assert_parse_error(self):
        """
        Asserts that the logger was called when the
        SafeCookieData object could not be parsed successfully.
        """
        with self.assert_logged('SafeCookieData BWC parse error'):
            yield

    @contextmanager
    def assert_invalid_session_id(self):
        """
        Asserts that the logger was called when a
        SafeCookieData was created with a Falsey value for
        the session_id.
        """
        with self.assert_logged('SafeCookieData not created due to invalid value for session_id'):
            yield

    @contextmanager
    def assert_request_user_mismatch(self, user_at_request, user_at_response):
        """
        Asserts that the logger was called when request.user at request
        time doesn't match the request.user at response time.
        """
        with self.assert_logged(
            "SafeCookieData user at request '{}' does not match user at response: '{}'".format(
                user_at_request, user_at_response
            ),
            log_level='warning',
        ):
            yield

    @contextmanager
    def assert_session_user_mismatch(self, user_at_request, user_in_session):
        """
        Asserts that the logger was called when request.user at request
        time doesn't match the request.user at response time.
        """
        with self.assert_logged(
            "SafeCookieData user at request '{}' does not match user in session: '{}'".format(
                user_at_request, user_in_session
            ),
        ):
            yield
