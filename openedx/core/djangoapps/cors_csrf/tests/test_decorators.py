"""Tests for cross-domain CSRF decorators. """


import json
from unittest import mock
from django.http import HttpResponse
from django.test import TestCase

from ..decorators import ensure_csrf_cookie_cross_domain


def fake_view(request):
    """Fake view that returns the request META as a JSON-encoded string. """
    return HttpResponse(json.dumps(request.META))  # lint-amnesty, pylint: disable=http-response-with-json-dumps


class TestEnsureCsrfCookieCrossDomain(TestCase):
    """Test the `ensure_csrf_cookie_cross_domain` decorator. """

    def test_ensure_csrf_cookie_cross_domain(self):
        request = mock.Mock()
        request.META = {}
        request.COOKIES = {}
        wrapped_view = ensure_csrf_cookie_cross_domain(fake_view)
        response = wrapped_view(request)
        response_meta = json.loads(response.content.decode('utf-8'))
        assert response_meta['CROSS_DOMAIN_CSRF_COOKIE_USED'] is True
        # In Django 3.2, it's CSRF_COOKIE_USED; as of 4.0 it's CSRF_COOKIE_NEEDS_UPDATE.
        # After upgrade to Django 4.2, delete the first clause.
        assert response_meta.get('CSRF_COOKIE_USED', response.meta.get('CSRF_COOKIE_NEEDS_UPDATE')) is True
