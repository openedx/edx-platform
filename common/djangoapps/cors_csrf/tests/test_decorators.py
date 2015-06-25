"""Tests for cross-domain CSRF decorators. """
import json
import mock
from django.http import HttpResponse
from django.test import TestCase
from cors_csrf.decorators import ensure_csrf_cookie_cross_domain


def fake_view(request):
    """Fake view that returns the request META as a JSON-encoded string. """
    return HttpResponse(json.dumps(request.META))


class TestEnsureCsrfCookieCrossDomain(TestCase):
    """Test the `ensucre_csrf_cookie_cross_domain` decorator. """

    def test_ensure_csrf_cookie_cross_domain(self):
        request = mock.Mock()
        request.META = {}
        wrapped_view = ensure_csrf_cookie_cross_domain(fake_view)
        response = wrapped_view(request)
        response_meta = json.loads(response.content)
        self.assertEqual(response_meta['CROSS_DOMAIN_CSRF_COOKIE_USED'], True)
        self.assertEqual(response_meta['CSRF_COOKIE_USED'], True)
