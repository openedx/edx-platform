"""Tests for IP determination"""

import warnings
from contextlib import contextmanager

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

import openedx.core.djangoapps.util.ip as ip


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
        ({}, 'Something', []),
        ({'HTTP_SOME_THING': 'stuff'}, 'Some-Thing', ['stuff']),
        ({'HTTP_SOME_THING': 'stuff'}, 'Some-Thing', ['stuff']),
        ({'HTTP_SOME_THING': '   so,much , stuff '}, 'Some-Thing', ['so', 'much', 'stuff']),
    )
    def test_get_meta_ips(self, add_meta, header_name, expected):
        self.request.META.update(add_meta)
        assert ip.get_meta_ips(self.request.META, header_name) == expected

    @ddt.unpack
    @ddt.data(
        # Header missing
        ({}, 'Some-Thing', 0, None, "missing"),
        # Header present, index out of range
        ({'HTTP_SOME_THING': '1.2.3.4'}, 'Some-Thing', 1, None, "out of range"),
        ({'HTTP_SOME_THING': '1.2.3.4'}, 'Some-Thing', -2, None, "out of range"),
        # Happy path
        ({'HTTP_SOME_THING': '1.2.3.4'}, 'Some-Thing', 0, '1.2.3.4', None),
        ({'HTTP_SOME_THING': '::6, ::5, ::4, ::3, ::2, ::1'}, 'Some-Thing', -2, '::2', None),
    )
    def test_get_by_one_header(self, add_meta, header_name, index, expected, warning_substr):
        self.request.META.update(add_meta)

        with warning_messages() as caught_warnings:
            actual = ip.get_client_ip_by_one_header(self.request.META, header_name, index)

        assert actual == expected

        if warning_substr is None:
            assert len(caught_warnings) == 0
        else:
            assert len(caught_warnings) == 1
            assert warning_substr in caught_warnings[0]

    @ddt.unpack
    @ddt.data(
        # No config
        ({}, [], None, 0),
        # Configured, but none of the headers are present
        (
            {},
            [
                {'name': 'CF-Connecting-IP', 'index': 0},
                {'name': 'X-Forwarded-For', 'index': -2},
                {'name': 'X-Real-IP', 'index': 0},
            ],
            None,
            3,
        ),
        # One lookup failure before finding a usable header
        (
            {
                'HTTP_X_FORWARDED_FOR': '1.1.1.1, 2.2.2.2, 3.3.3.3, 4.4.4.4'
            },
            [
                {'name': 'CF-Connecting-IP', 'index': 0},
                {'name': 'X-Forwarded-For', 'index': -2},
                {'name': 'X-Real-IP', 'index': 0},
            ],
            '3.3.3.3',
            1,
        ),
    )
    def test_get_via_configured_headers(self, add_meta, cnf_headers, expected, warning_count):
        self.request.META.update(add_meta)

        with override_settings(**{'CLIENT_IP_HEADERS': cnf_headers}):
            with warning_messages() as caught_warnings:
                actual = ip.get_client_ip_via_configured_headers(self.request.META)

        assert actual == expected
        assert len(caught_warnings) == warning_count

    @ddt.unpack
    @ddt.data(
        # Nothing usable
        ([], None),
        (['any-old-junk'], None),
        # Simple cases, private and public
        (['::1'], '::1'),
        (['1.2.3.4'], '1.2.3.4'),
        # If we get a public IP, don't worry about junk farther on
        (['junk', '1.2.3.4', '2606:4700::'], '2606:4700::'),
        (['junk', '2606:4700::', '10.0.0.1'], '2606:4700::'),
        # Walk left until first public IP
        (['1.2.3.4', '5.6.7.8', '10.0.0.1', '127.0.0.1'], '5.6.7.8'),
        # Or until there's junk, even if the best we can do is a private IP
        (['1.2.3.4', 'XXXXXXX', '10.0.0.1', '127.0.0.1'], '10.0.0.1'),
    )
    def test_conservative_walk(self, chain, expected):
        assert ip.conservatively_pick_client_ip(chain) == expected

    @ddt.unpack
    @ddt.data(
        # Publicly exposed server, perhaps
        ({'REMOTE_ADDR': '4.3.2.1'}, '4.3.2.1'),
        # ...maybe with someone trying to spoof their IP
        ({'HTTP_X_FORWARDED_FOR': '5.5.5.5', 'REMOTE_ADDR': '4.3.2.1'}, '4.3.2.1'),
        # If XFF is missing, just accept a private IP
        ({'REMOTE_ADDR': '127.0.0.1'}, '127.0.0.1'),
        # General case, walk from right
        ({'HTTP_X_FORWARDED_FOR': '8.7.6.5, 4.3.2.1, 10.0.0.1', 'REMOTE_ADDR': '127.0.0.1'}, '4.3.2.1'),
    )
    def test_get_via_xff(self, add_meta, expected):
        self.request.META.update(add_meta)
        assert ip.get_client_ip_via_xff(self.request.META) == expected

    @ddt.unpack
    @ddt.data(
        # By default, do something useful
        (None, {'REMOTE_ADDR': '127.0.0.2'}, '127.0.0.2', 0),
        # Can use arbitrary headers
        (
            [{'name': 'CF-Connecting-IP', 'index': 0}],
            {'HTTP_X_FORWARDED_FOR': '4.3.2.1', 'HTTP_CF_CONNECTING_IP': '5.6.7.8', 'REMOTE_ADDR': '127.0.0.2'},
            '5.6.7.8',
            0,
        ),
        # Fall back when all override headers are unusable, with warnings
        (
            [
                {'name': 'CF-Connecting-IP', 'index': 0},  # not actually passed in this request
                {'name': 'X-Real-IP', 'index': 2},  # index out of range, so unusable
            ],
            {
                'HTTP_X_FORWARDED_FOR': '5.6.7.8, 4.3.2.1, 137.0.55.99, 10.0.0.8',
                'HTTP_X_REAL_IP': '101.102.3.4',
                'REMOTE_ADDR': '127.0.0.2',
            },
            '137.0.55.99',
            2,
        ),
        # Our idiosyncratic ORIGINAL_REMOTE_ADDR takes precedence
        (
            None,
            {'ORIGINAL_REMOTE_ADDR': '4.3.2.1', 'REMOTE_ADDR': '5.5.5.5'},
            '4.3.2.1',
            0,
        ),
    )
    def test_get_client_ip(self, cnf_headers, add_meta, expected, expect_warnings):
        """
        Just a few tests to confirm that the correct branch is taken, basically.
        """
        if cnf_headers is None:
            overrides = {}
        else:
            overrides = {'CLIENT_IP_HEADERS': cnf_headers}

        self.request.META.update(add_meta)

        with override_settings(**overrides):
            with warning_messages() as caught_warnings:
                actual = ip.get_client_ip(self.request)

        assert actual == expected
        assert len(caught_warnings) == expect_warnings
