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

import warnings
from contextlib import contextmanager

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

import openedx.core.djangoapps.util.ip as ip
from openedx.core.lib.x_forwarded_for.middleware import XForwardedForMiddleware


@contextmanager
def warning_messages():
    """
    Context manager which produces a list of warning messages as the context
    value (only populated after block ends).
    """
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        messages = []
        yield messages
        # Converted to message strings for easier debugging
        messages.extend(str(w.message) for w in caught_warnings)


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
        assert ip.get_legacy_ip(self.request) == expected

        # Check that it still works after the XFF middleware has done its dirty work
        XForwardedForMiddleware().process_request(self.request)
        assert ip.get_legacy_ip(self.request) == expected

    @ddt.unpack
    @ddt.data(
        ({}, 'Some-Thing', []),
        ({'HTTP_SOME_THING': 'stuff'}, 'Some-Thing', ['stuff']),
        ({'HTTP_SOME_THING': 'stuff'}, 'Some-Thing', ['stuff']),
        ({'HTTP_SOME_THING': '   so,much , stuff '}, 'Some-Thing', ['so', 'much', 'stuff']),
    )
    def test_get_meta_ip_strs(self, add_meta, header_name, expected):
        self.request.META.update(add_meta)
        assert ip._get_meta_ip_strs(self.request, header_name) == expected  # pylint: disable=protected-access

    @ddt.unpack
    @ddt.data(
        # Form the IP chain and parse it (notice the IPv6 is canonicalized)
        (
            {'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 10.0.3.0', 'REMOTE_ADDR': '0:0:0:0::1'},
            ['7.8.9.0', '1.2.3.4', '10.0.3.0', '::1'],
        ),

        # XFF is not required
        ({'REMOTE_ADDR': '127.0.0.2'}, ['127.0.0.2']),

        # Strips off junk and anything to the left of it
        (
            {
                'HTTP_X_FORWARDED_FOR': '6.6.6.6, XXXXXXXXX, 7.8.9.0, XXXXXXXXX, 1.2.3.4',
                'REMOTE_ADDR': '10.0.3.0'
            },
            ['1.2.3.4', '10.0.3.0'],
        ),
    )
    def test_get_usable_ip_chain(self, request_meta, expected_strs):
        self.request.META = request_meta
        actual_ips = ip._get_usable_ip_chain(self.request)  # pylint: disable=protected-access
        assert [str(ip) for ip in actual_ips] == expected_strs

    @ddt.unpack
    @ddt.data(
        # Empty returns empty
        ([], lambda x: False, []),
        ([], lambda x: True, []),

        # Can return whole list or remove all of it
        ([1, 2, 3, 4], lambda x: False, [1, 2, 3, 4]),
        ([1, 2, 3, 4], lambda x: True, []),

        # Walks from right, stops on first false, keeps that element
        ([2, 0, 1, 0, 3, 5], lambda x: x != 0, [2, 0, 1, 0]),
    )
    def test_remove_tail(self, elements, f_discard, expected):
        assert ip._remove_tail(elements, f_discard) == expected  # pylint: disable=protected-access

    @ddt.unpack
    @ddt.data(
        # Walk from right, dropping private-range IPs
        ('7:8:9:0::, 1.2.3.4, 10.0.3.0', '::1', ['7:8:9::', '1.2.3.4']),
        ('7.8.9.0', '1.2.3.4', ['7.8.9.0', '1.2.3.4']),

        # Publicly exposed server (no XFF added by proxies)
        (None, '1.2.3.4', ['1.2.3.4']),

        # If XFF is missing, just accept a private IP (maybe an inter-service call
        # from another server in the same datacenter)
        (None, '127.0.0.2', ['127.0.0.2']),

        # If we reach a public IP, don't worry about junk farther on
        ('XXXXXXXXX, 1:2:3:4::', '10.0.0.1', ['1:2:3:4::']),

        # If we find junk or we run out of IPs before finding a public
        # one, the best we can do is a private IP. (Should never
        # happen for a public IP, but here for completeness.)
        ('7.8.9.0, XXXXXXXXX, 10.0.3.0', '127.0.0.2', ['10.0.3.0']),
        (None, '::1', ['::1']),

        # Nothing usable (again, should never happen)
        (None, '', []),
        (None, 'XXXXXXXXX', []),
        ('1.2.3.4', 'XXXXXXXXX', []),
    )
    def test_get_client_ips_via_xff(self, xff, remote_addr, expected_strs):
        request_meta = {'REMOTE_ADDR': remote_addr, 'HTTP_X_FORWARDED_FOR': xff}
        request_meta = {k: v for k, v in request_meta.items() if v is not None}
        self.request.META = request_meta

        assert [str(ip) for ip in ip._get_client_ips_via_xff(self.request)] == expected_strs  # pylint: disable=protected-access

    @ddt.unpack
    @ddt.data(
        # Happy path
        ('Some-Thing', 0, {'HTTP_SOME_THING': '1.2.3.4'}, '1.2.3.4', None),
        ('some-thing', -1, {'HTTP_SOME_THING': '1:2:3:4::, 0:0::1'}, '::1', None),

        # Warning: Header present, index out of range
        ('Some-Thing', 1, {'HTTP_SOME_THING': '1.2.3.4'}, None, "out of range"),
        ('Some-Thing', -2, {'HTTP_SOME_THING': '1.2.3.4'}, None, "out of range"),

        # Warning: Header missing entirely
        ('Some-Thing', 0, {}, None, "missing"),

        # Warning: Bad IP address
        ('Some-Thing', 0, {'HTTP_SOME_THING': 'XXXXXXXXX'}, None, "invalid IP"),
    )
    def test_get_trusted_header_ip(self, header_name, index, add_meta, expected, warning_substr):
        self.request.META.update(add_meta)

        with warning_messages() as caught_warnings:
            actual = ip._get_trusted_header_ip(self.request, header_name, index)  # pylint: disable=protected-access

        if expected is None:
            assert actual is None
        else:
            assert str(actual) == expected  # Stringify again for comparison

        if warning_substr is None:
            assert len(caught_warnings) == 0
        else:
            assert len(caught_warnings) == 1
            assert warning_substr in caught_warnings[0]

    @ddt.unpack
    @ddt.data(
        # Most common case: One header in config, and header does exist
        (
            [{'name': 'CF-Connecting-IP', 'index': 0}],
            {
                'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                'REMOTE_ADDR': '10.0.3.0',
                'HTTP_CF_CONNECTING_IP': '1.2.3.4',
            },
            ['1.2.3.4'],
            0,
        ),
        # More complicated version with intervening proxies and a spoofed IP
        (
            [{'name': 'CF-Connecting-IP', 'index': 0}],
            {
                'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 5.5.5.5, 10.0.3.0',
                'REMOTE_ADDR': '127.0.0.2',
                'HTTP_CF_CONNECTING_IP': '  1.2.3.4  ',  # tests that whitespace is stripped
            },
            ['7.8.9.0', '1.2.3.4'],
            0,
        ),

        # Uses *rightmost* position of identified IP if multiple are present
        # (prevent spoofing when client calling through a trustworthy proxy)
        (
            [{'name': 'CF-Connecting-IP', 'index': 0}],
            {
                'HTTP_X_FORWARDED_FOR': '6.6.6.6, 1.2.3.4, 7.8.9.0, 1.2.3.4, 5.5.5.5',
                'REMOTE_ADDR': '10.0.3.0',
                'HTTP_CF_CONNECTING_IP': '1.2.3.4',
            },
            ['6.6.6.6', '1.2.3.4', '7.8.9.0', '1.2.3.4'],
            0,
        ),

        # No config? Empty list.
        ([], {'REMOTE_ADDR': '1.2.3.4'}, [], 0),
        (None, {'REMOTE_ADDR': '1.2.3.4'}, [], 0),

        # One lookup failure (a warning) before finding a usable header
        (
            [
                {'name': 'X-Real-IP', 'index': 0},
                {'name': 'CF-Connecting-IP', 'index': 0},
            ],
            {
                'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 5.5.5.5',
                'REMOTE_ADDR': '10.0.3.0',
                'HTTP_CF_CONNECTING_IP': '1.2.3.4',
            },
            ['7.8.9.0', '1.2.3.4'],
            1,
        ),

        # Configured, but none of the headers are present
        (
            [
                {'name': 'CF-Connecting-IP', 'index': 0},
                {'name': 'X-Forwarded-For', 'index': -2},
            ],
            {'REMOTE_ADDR': '1.2.3.4'},
            [],
            2,
        ),

        # Can configure to use far end of XFF if needed for some reason
        (
            [
                {'name': 'X-Forwarded-For', 'index': 0},
            ],
            {
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 5.5.5.5',
                'REMOTE_ADDR': '10.0.3.0',
            },
            ['1.2.3.4'],
            0,
        ),
    )
    def test_get_client_ips_via_trusted_header(self, cnf_headers, add_meta, expected, warning_count):
        self.request.META.update(add_meta)
        if cnf_headers is None:
            overrides = {}
        else:
            overrides = {'CLOSEST_CLIENT_IP_FROM_HEADERS': cnf_headers}

        with override_settings(**overrides):
            with warning_messages() as caught_warnings:
                actual = ip._get_client_ips_via_trusted_header(self.request)  # pylint: disable=protected-access

        assert [str(ip) for ip in actual] == expected
        assert len(caught_warnings) == warning_count

    @ddt.unpack
    @ddt.data(
        # Using headers setting
        (
            [{'name': 'CF-Connecting-IP', 'index': 0}],
            {
                'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 5.5.5.5, 10.0.3.0',
                'HTTP_CF_CONNECTING_IP': '1.2.3.4',
                'REMOTE_ADDR': '127.0.0.2',
            },
            ['7.8.9.0', '1.2.3.4'],
            0,
        ),

        # Fall back when all override headers are unusable, with warnings
        (
            [
                {'name': 'CF-Connecting-IP', 'index': 0},  # not actually passed in this request
                {'name': 'X-Real-IP', 'index': 2},  # index out of range, so unusable
            ],
            {
                'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4, 10.0.3.0, 127.0.0.2',
                'HTTP_X_REAL_IP': '10.0.3.0',
                'REMOTE_ADDR': '127.0.0.2',
            },
            ['7.8.9.0', '1.2.3.4'],
            2,
        ),

        # By default, with the least possible information, do something useful.
        # (And no warnings when no override headers are specified.)
        ([], {'REMOTE_ADDR': '127.0.0.2'}, ['127.0.0.2'], 0),
    )
    def test_compute_client_ips(self, cnf_headers, add_meta, expected, expect_warnings):
        """
        Just a few tests to confirm that the correct branch is taken, basically.
        """
        if cnf_headers is None:
            overrides = {}
        else:
            overrides = {'CLOSEST_CLIENT_IP_FROM_HEADERS': cnf_headers}

        self.request.META.update(add_meta)

        with override_settings(**overrides):
            with warning_messages() as caught_warnings:
                actual = ip._compute_client_ips(self.request)  # pylint: disable=protected-access

        assert actual == expected
        assert len(caught_warnings) == expect_warnings

    def test_get_all_client_ips(self):
        """
        Test getter for all IPs.
        """
        self.request.META.update({
            'HTTP_X_FORWARDED_FOR': '7.8.9.0, 1.2.3.4',
            'REMOTE_ADDR': '127.0.0.2',
        })

        assert ip.get_all_client_ips(self.request) == ['7.8.9.0', '1.2.3.4']

    def test_get_safest_client_ip(self):
        """
        Test convenience wrapper for rightmost IP.
        """
        self.request.META.update({
            'HTTP_X_FORWARDED_FOR': '7.8.9.0',
            'REMOTE_ADDR': '1.2.3.4',
        })

        assert ip.get_safest_client_ip(self.request) == '1.2.3.4'
