"""
Tests for rate-limiting.
"""

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from edx_toggles.toggles.testutils import override_waffle_switch

import openedx.core.djangoapps.util.ratelimit as ratelimit
from openedx.core.lib.x_forwarded_for.middleware import XForwardedForMiddleware


@ddt.ddt
class TestRateLimiting(TestCase):
    """Tests for rate limiting and helpers."""
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get('/somewhere')
        self.request.META.update({
            'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 10.0.3.0',
            'REMOTE_ADDR': '127.0.0.2',
        })

    def test_real_ip(self):
        """
        Bare test, no middleware to init the external chain.
        """
        assert ratelimit.real_ip(None, self.request) == '1.2.3.4'

    def test_real_ip_after_xff_middleware(self):
        """
        More realistic test since XFF middleware meddles with REMOTE_ADDR.
        """
        XForwardedForMiddleware().process_request(self.request)
        assert ratelimit.real_ip(None, self.request) == '1.2.3.4'

    @override_waffle_switch(ratelimit.ip.USE_LEGACY_IP, True)
    def test_legacy_switch(self):
        assert ratelimit.real_ip(None, self.request) == '7.8.9.0'

    @override_waffle_switch(ratelimit.ip.USE_LEGACY_IP, True)
    def test_legacy_switch_after_xff_middleware(self):
        """
        Again, but with XFF Middleware running first.
        """
        XForwardedForMiddleware().process_request(self.request)
        assert ratelimit.real_ip(None, self.request) == '7.8.9.0'
