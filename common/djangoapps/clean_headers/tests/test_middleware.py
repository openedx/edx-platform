"""Tests for clean_headers middleware."""
from django.http import HttpResponse, HttpRequest
from django.test import TestCase
from clean_headers.middleware import CleanHeadersMiddleware


class TestCleanHeadersMiddlewareProcessResponse(TestCase):
    """Test the `clean_headers` middleware. """
    def setUp(self):
        super(TestCleanHeadersMiddlewareProcessResponse, self).setUp()
        self.middleware = CleanHeadersMiddleware()

    def test_cleans_intended_headers(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'
        fake_response.clean_headers = ['Vary']

        result = self.middleware.process_response(fake_request, fake_response)
        self.assertNotIn('Vary', result)
        self.assertEquals('gzip', result['Accept-Encoding'])

    def test_does_not_mangle_undecorated_response(self):
        fake_request = HttpRequest()

        fake_response = HttpResponse()
        fake_response['Vary'] = 'Cookie'
        fake_response['Accept-Encoding'] = 'gzip'

        result = self.middleware.process_response(fake_request, fake_response)
        self.assertEquals('Cookie', result['Vary'])
        self.assertEquals('gzip', result['Accept-Encoding'])
