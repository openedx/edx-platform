"""
Test Custom Exceptions
"""

import ddt
from django.test import TestCase
from rest_framework import exceptions as drf_exceptions


@ddt.ddt
class TestDictExceptionsAllowDictDetails(TestCase):
    """
    Test that standard DRF exceptions can return dictionaries in error details.
    """

    def test_drf_errors_are_not_coerced_to_strings(self):
        # Demonstrate that dictionaries in exceptions are not coerced to strings.
        exc = drf_exceptions.AuthenticationFailed({'error_code': -1})
        assert not isinstance(exc.detail, str)

    @ddt.data(
        drf_exceptions.AuthenticationFailed,
        drf_exceptions.NotAuthenticated,
        drf_exceptions.NotFound,
        drf_exceptions.ParseError,
        drf_exceptions.PermissionDenied,
    )
    def test_exceptions_allows_dict_detail(self, exception_class):
        exc = exception_class({'error_code': -1})
        assert exc.detail == {'error_code': '-1'}

    def test_method_not_allowed_allows_dict_detail(self):
        exc = drf_exceptions.MethodNotAllowed('POST', {'error_code': -1})
        assert exc.detail == {'error_code': '-1'}

    def test_not_acceptable_allows_dict_detail(self):
        exc = drf_exceptions.NotAcceptable({'error_code': -1}, available_renderers=['application/json'])
        assert exc.detail == {'error_code': '-1'}
        assert exc.available_renderers == ['application/json']
