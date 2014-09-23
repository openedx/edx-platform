"""
Tests for helper functions.
"""
import mock
from django.test import TestCase
from nose.tools import raises
from user_api.helpers import intercept_errors


class FakeInputException(Exception):
    """Fake exception that should be intercepted. """
    pass


class FakeOutputException(Exception):
    """Fake exception that should be raised. """
    pass


@intercept_errors(FakeOutputException, ignore_errors=[ValueError])
def intercepted_function(raise_error=None):
    """Function used to test the intercept error decorator.

    Keyword Arguments:
        raise_error (Exception): If provided, raise this exception.

    """
    if raise_error is not None:
        raise raise_error


class InterceptErrorsTest(TestCase):
    """
    Tests for the decorator that intercepts errors.
    """

    @raises(FakeOutputException)
    def test_intercepts_errors(self):
        intercepted_function(raise_error=FakeInputException)

    def test_ignores_no_error(self):
        intercepted_function()

    @raises(ValueError)
    def test_ignores_expected_errors(self):
        intercepted_function(raise_error=ValueError)

    @mock.patch('user_api.helpers.LOGGER')
    def test_logs_errors(self, mock_logger):
        expected_log_msg = (
            u"An unexpected error occurred when calling 'intercepted_function' "
            u"with arguments '()' and "
            u"keyword arguments '{'raise_error': <class 'user_api.tests.test_helpers.FakeInputException'>}': "
            u"FakeInputException()"
        )

        # Verify that the raised exception has the error message
        try:
            intercepted_function(raise_error=FakeInputException)
        except FakeOutputException as ex:
            self.assertEqual(ex.message, expected_log_msg)

        # Verify that the error logger is called
        # This will include the stack trace for the original exception
        # because it's called with log level "ERROR"
        mock_logger.exception.assert_called_once_with(expected_log_msg)
