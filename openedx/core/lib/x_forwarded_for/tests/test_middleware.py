"""
Tests for XForwardedForMiddleware.
"""

from unittest.mock import call, patch

import ddt
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.lib.x_forwarded_for.middleware import XForwardedForMiddleware


@ddt.ddt
class TestXForwardedForMiddleware(TestCase):
    """Tests for middleware's overrides."""

    @ddt.unpack
    @ddt.data(
        # With no added headers, just see the test server's defaults.
        (
            {},
            {
                'SERVER_NAME': 'testserver',
                'SERVER_PORT': '80',
                'REMOTE_ADDR': '127.0.0.1',
            },
        ),
        # With headers supplied by the request (Host) and a proxy
        # (X-Forwarded-Port), see the name and port overridden.
        (
            {
                'HTTP_HOST': 'example.com',
                'HTTP_X_FORWARDED_PORT': '443',
            },
            {
                'SERVER_NAME': 'example.com',
                'SERVER_PORT': '443',
            },
        ),

        # REMOTE_ADDR can also be overridden (chooses rightmost)
        (
            {'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4'},
            {
                'REMOTE_ADDR': '1.2.3.4',
            },
        ),
    )
    def test_overrides(self, add_meta, expected_meta_include):
        """
        Test that parts of request.META can be overridden by HTTP headers.
        """
        request = RequestFactory().get('/somewhere')
        request.META.update(add_meta)

        XForwardedForMiddleware().process_request(request)

        assert request.META.items() >= expected_meta_include.items()

    @ddt.unpack
    @ddt.data(
        (None, '127.0.0.1', 1, 'priv'),
        ('1.2.3.4', '1.2.3.4, 127.0.0.1', 2, 'pub-priv'),
        ('XXXXXXXX, 1.2.3.4, 5.5.5.5', 'XXXXXXXX, 1.2.3.4, 5.5.5.5, 127.0.0.1', 4, 'unknown-pub-pub-priv'),
    )
    @patch("openedx.core.lib.x_forwarded_for.middleware.set_custom_attribute")
    def test_xff_metrics(self, xff, expected_raw, expected_count, expected_types, mock_set_custom_attribute):
        request = RequestFactory().get('/somewhere')
        if xff is not None:
            request.META['HTTP_X_FORWARDED_FOR'] = xff

        XForwardedForMiddleware().process_request(request)

        mock_set_custom_attribute.assert_has_calls([
            call('ip_chain.raw', expected_raw),
            call('ip_chain.count', expected_count),
            call('ip_chain.types', expected_types),
        ])
