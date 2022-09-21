"""
Tests for IP determination.

Fake data used in these tests, for consistency:

- 1.2.3.4 -- a "real" client IP, e.g. the IP of a laptop or phone.
- 127.0.0.2 -- a local reverse proxy (e.g. nginx or caddy)
- 10.0.3.0 -- our load balancer
- 5.5.5.5 -- our CDN
- 6.6.6.6 -- a malicious CDN configuration
- 7.8.9.0 -- something beyond the real client in the IP chain, probably a spoofed header

...as well as IPv6 versions of these, e.g. 1:2:3:4:: and ::1.

XXXXXXXXX is used as a standin for anything unparseable (some kind of garbage).
"""

import ddt
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.util import legacy_ip
from openedx.core.lib.x_forwarded_for.middleware import XForwardedForMiddleware


@ddt.ddt
class TestClientIP(TestCase):
    """Tests for get_client_ip and helpers."""

    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get('/somewhere')

    @ddt.unpack
    @ddt.data(
        (
            {'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 10.0.3.0', 'REMOTE_ADDR': '0:0:0:0::1'},
            '7.8.9.0',
        ),

        # XFF is not required
        ({'REMOTE_ADDR': '127.0.0.2'}, '127.0.0.2'),
    )
    def test_get_legacy_ip(self, request_meta, expected):
        self.request.META = request_meta
        assert legacy_ip.get_legacy_ip(self.request) == expected

        # Check that it still works after the XFF middleware has done its dirty work
        XForwardedForMiddleware().process_request(self.request)
        assert legacy_ip.get_legacy_ip(self.request) == expected
