"""
Test Custom Exceptions
"""

import ddt
from django.test import TestCase
from rest_framework import exceptions as drf_exceptions
import six


@ddt.ddt
class TestDictExceptionsAllowDictDetails(TestCase):
    """
    Test that standard DRF exceptions can return dictionaries in error details.
    """

    def test_drf_errors_are_not_coerced_to_strings(self):
        # Demonstrate that dictionaries in exceptions are not coerced to strings.
        exc = drf_exceptions.AuthenticationFailed({u'error_code': -1})
        self.assertNotIsInstance(exc.detail, six.string_types)

    @ddt.data(
        drf_exceptions.AuthenticationFailed,
        drf_exceptions.NotAuthenticated,
        drf_exceptions.NotFound,
        drf_exceptions.ParseError,
        drf_exceptions.PermissionDenied,
    )
    def test_exceptions_allows_dict_detail(self, exception_class):
        exc = exception_class({u'error_code': -1})
        self.assertEqual(exc.detail, {u'error_code': u'-1'})

    def test_method_not_allowed_allows_dict_detail(self):
        exc = drf_exceptions.MethodNotAllowed(u'POST', {u'error_code': -1})
        self.assertEqual(exc.detail, {u'error_code': u'-1'})

    def test_not_acceptable_allows_dict_detail(self):
        exc = drf_exceptions.NotAcceptable({u'error_code': -1}, available_renderers=['application/json'])
        self.assertEqual(exc.detail, {u'error_code': u'-1'})
        self.assertEqual(exc.available_renderers, ['application/json'])
