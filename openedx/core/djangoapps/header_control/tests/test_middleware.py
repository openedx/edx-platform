"""Tests for header_control middleware."""


from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from openedx.core.djangoapps.header_control import force_header_for_response, remove_headers_from_response
from openedx.core.djangoapps.header_control.middleware import HeaderControlMiddleware


class TestHeaderControlMiddlewareProcessResponse(TestCase):
    """Test the `header_control` middleware. """
    def setUp(self):
        super().setUp()
        self.middleware = HeaderControlMiddleware()

    def test_doesnt_barf_if_not_modifying_anything(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'

        result = self.middleware.process_response(fake_request, fake_response)
        assert 'Cookie' == result['Vary']
        assert 'gzip' == result['Accept-Encoding']

    def test_doesnt_barf_removing_nonexistent_headers(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'
        remove_headers_from_response(fake_response, 'Vary', 'FakeHeaderWeeee')

        result = self.middleware.process_response(fake_request, fake_response)
        assert 'Vary' not in result
        assert 'gzip' == result['Accept-Encoding']

    def test_removes_intended_headers(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'
        remove_headers_from_response(fake_response, 'Vary')

        result = self.middleware.process_response(fake_request, fake_response)
        assert 'Vary' not in result
        assert 'gzip' == result['Accept-Encoding']

    def test_forces_intended_header(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'
        force_header_for_response(fake_response, 'Vary', 'Origin')

        result = self.middleware.process_response(fake_request, fake_response)
        assert 'Origin' == result['Vary']
        assert 'gzip' == result['Accept-Encoding']

    def test_does_not_mangle_undecorated_response(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'

        result = self.middleware.process_response(fake_request, fake_response)
        assert 'Cookie' == result['Vary']
        assert 'gzip' == result['Accept-Encoding']
