"""
Tests for the request cache.
"""
from django.conf import settings
from django.test import TestCase

from request_cache import get_request_or_stub


class TestRequestCache(TestCase):
    """
    Tests for the request cache.
    """

    def test_get_request_or_stub(self):
        # Outside the context of the request, we should still get a request
        # that allows us to build an absolute URI.
        stub = get_request_or_stub()
        expected_url = "http://{site_name}/foobar".format(site_name=settings.SITE_NAME)
        self.assertEqual(stub.build_absolute_uri("foobar"), expected_url)
