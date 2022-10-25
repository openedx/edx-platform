"""Tests for remove_headers and force_header decorator. """


from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from openedx.core.djangoapps.header_control.decorators import force_header, remove_headers


def fake_view(_request):
    """Fake view that returns an empty response."""
    return HttpResponse()


class TestRemoveHeaders(TestCase):
    """Test the `remove_headers` decorator."""

    def test_remove_headers(self):
        request = HttpRequest()
        wrapper = remove_headers('Vary', 'Accept-Encoding')
        wrapped_view = wrapper(fake_view)
        response = wrapped_view(request)
        assert len(response.remove_headers) == 2


class TestForceHeader(TestCase):
    """Test the `force_header` decorator."""

    def test_force_header(self):
        request = HttpRequest()
        wrapper = force_header('Vary', 'Origin')
        wrapped_view = wrapper(fake_view)
        response = wrapped_view(request)
        assert len(response.force_headers) == 1
        assert response.force_headers['Vary'] == 'Origin'
