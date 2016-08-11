"""
Test Custom Exceptions
"""
import ddt
from django.test import TestCase
from nose.plugins.attrib import attr
from rest_framework import exceptions as drf_exceptions

from .. import exceptions


@attr(shard=2)
@ddt.ddt
class TestDictExceptionsAllowDictDetails(TestCase):
    """
    Standard DRF exceptions coerce detail inputs to strings.  We want to use
    dicts to allow better customization of error messages.  Demonstrate that
    we can provide dictionaries as exception details, and that custom
    classes subclass the relevant DRF exceptions, to provide consistent
    exception catching behavior.
    """

    def test_drf_errors_coerce_strings(self):
        # Demonstrate the base issue we are trying to solve.
        exc = drf_exceptions.AuthenticationFailed({u'error_code': -1})
        self.assertEqual(exc.detail, u"{u'error_code': -1}")

    @ddt.data(
        exceptions.AuthenticationFailed,
        exceptions.NotAuthenticated,
        exceptions.NotFound,
        exceptions.ParseError,
        exceptions.PermissionDenied,
    )
    def test_exceptions_allows_dict_detail(self, exception_class):
        exc = exception_class({u'error_code': -1})
        self.assertEqual(exc.detail, {u'error_code': -1})

    def test_method_not_allowed_allows_dict_detail(self):
        exc = exceptions.MethodNotAllowed(u'POST', {u'error_code': -1})
        self.assertEqual(exc.detail, {u'error_code': -1})

    def test_not_acceptable_allows_dict_detail(self):
        exc = exceptions.NotAcceptable({u'error_code': -1}, available_renderers=['application/json'])
        self.assertEqual(exc.detail, {u'error_code': -1})
        self.assertEqual(exc.available_renderers, ['application/json'])


@attr(shard=2)
@ddt.ddt
class TestDictExceptionSubclassing(TestCase):
    """
    Custom exceptions should subclass standard DRF exceptions, so code that
    catches the DRF exceptions also catches ours.
    """

    @ddt.data(
        (exceptions.AuthenticationFailed, drf_exceptions.AuthenticationFailed),
        (exceptions.NotAcceptable, drf_exceptions.NotAcceptable),
        (exceptions.NotAuthenticated, drf_exceptions.NotAuthenticated),
        (exceptions.NotFound, drf_exceptions.NotFound),
        (exceptions.ParseError, drf_exceptions.ParseError),
        (exceptions.PermissionDenied, drf_exceptions.PermissionDenied),
    )
    @ddt.unpack
    def test_exceptions_subclass_drf_exceptions(self, exception_class, drf_exception_class):
        exc = exception_class({u'error_code': -1})
        self.assertIsInstance(exc, drf_exception_class)

    def test_method_not_allowed_subclasses_drf_exception(self):
        exc = exceptions.MethodNotAllowed(u'POST', {u'error_code': -1})
        self.assertIsInstance(exc, drf_exceptions.MethodNotAllowed)
