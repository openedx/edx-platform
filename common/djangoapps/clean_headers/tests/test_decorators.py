"""Tests for clean_headers decorator. """
from django.http import HttpResponse, HttpRequest
from django.test import TestCase
from clean_headers.decorators import clean_headers


def fake_view(_request):
    """Fake view that returns an empty response."""
    return HttpResponse()


class TestCleanHeaders(TestCase):
    """Test the `clean_headers` decorator."""

    def test_clean_headers(self):
        request = HttpRequest()
        wrapper = clean_headers('Vary', 'Accept-Encoding')
        wrapped_view = wrapper(fake_view)
        response = wrapped_view(request)
        self.assertEqual(len(response.clean_headers), 2)
