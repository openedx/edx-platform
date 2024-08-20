"""
Tests for Content-Security-Policy middleware.
"""

from unittest import TestCase
from unittest.mock import Mock, patch

import ddt
import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.test import override_settings

import edx_django_utils.security.csp.middleware as csp


@ddt.ddt
class TestLoadHeaders(TestCase):
    """Test loading of headers from settings."""

    @ddt.unpack
    @ddt.data(
        # Empty settings
        [{}, {}],
        # The reporting URL and endpoint names alone don't do anything
        [{"CSP_STATIC_REPORTING_URI": "http://localhost"}, {}],
        [{"CSP_STATIC_REPORTING_NAME": "default"}, {}],
        [
            {
                "CSP_STATIC_REPORTING_URI": "http://localhost",
                "CSP_STATIC_REPORTING_NAME": "default"
            },
            {},
        ],
        # Just the enforcement header
        [
            {"CSP_STATIC_ENFORCE": "default-src https:"},
            {'Content-Security-Policy': "default-src https:"},
        ],
        # Just the reporting header
        [
            {"CSP_STATIC_REPORT_ONLY": "default-src 'none'"},
            {'Content-Security-Policy-Report-Only': "default-src 'none'"},
        ],
        # Reporting URL is automatically appended to headers
        [
            {
                "CSP_STATIC_ENFORCE": "default-src https:",
                "CSP_STATIC_REPORT_ONLY": "default-src 'none'",
                "CSP_STATIC_REPORTING_URI": "http://localhost",
            },
            {
                'Content-Security-Policy': "default-src https:; report-uri http://localhost",
                'Content-Security-Policy-Report-Only': "default-src 'none'; report-uri http://localhost",
            },
        ],
        # ...and when an endpoint name is supplied,
        # Reporting-Endpoints is added and a report-to directive is
        # included.
        [
            {
                "CSP_STATIC_ENFORCE": "default-src https:",
                "CSP_STATIC_REPORT_ONLY": "default-src 'none'",
                "CSP_STATIC_REPORTING_URI": "http://localhost",
                "CSP_STATIC_REPORTING_NAME": "default",
            },
            {
                'Reporting-Endpoints': 'default="http://localhost"',
                'Content-Security-Policy': "default-src https:; report-uri http://localhost; report-to default",
                'Content-Security-Policy-Report-Only': (
                    "default-src 'none'; report-uri http://localhost; report-to default"
                ),
            },
        ],
        # Adding a reporting endpoint name without a URL doesn't change anything.
        [
            {
                "CSP_STATIC_REPORT_ONLY": "default-src 'none'",
                "CSP_STATIC_REPORTING_NAME": "default",
            },
            {'Content-Security-Policy-Report-Only': "default-src 'none'"},
        ],
        # Any newlines and trailing semicolon are stripped.
        [
            {
                "CSP_STATIC_REPORT_ONLY": "default-src 'self';   \n \t  frame-src 'none';  \n ",
                "CSP_STATIC_REPORTING_URI": "http://localhost",
            },
            {
                'Content-Security-Policy-Report-Only': (
                    "default-src 'self'; frame-src 'none'; "
                    "report-uri http://localhost"
                ),
            },
        ],
    )
    def test_load_headers(self, settings, headers):
        with override_settings(**settings):
            assert csp._load_headers() == headers  # pylint: disable=protected-access


@ddt.ddt
class TestHeaderManipulation(TestCase):
    """Test _append_headers"""

    @ddt.unpack
    @ddt.data(
        [{}, {}, {}],
        [
            {'existing': 'aaa', 'multi': '111'},
            {'multi': '222', 'new': 'xxx'},
            {'existing': 'aaa', 'multi': '111, 222', 'new': 'xxx'},
        ],
    )
    def test_append_headers(self, response_headers, more_headers, expected):
        csp._append_headers(response_headers, more_headers)  # pylint: disable=protected-access
        assert response_headers == expected


@ddt.ddt
class TestCSPMiddleware(TestCase):
    """Test the actual middleware."""

    def setUp(self):
        super().setUp()
        self.fake_response = Mock()
        self.fake_response.headers = {'Existing': 'something'}

    def test_make_middleware_unused(self):
        with pytest.raises(MiddlewareNotUsed):
            csp.content_security_policy_middleware(lambda _: self.fake_response)

    @override_settings(CSP_STATIC_ENFORCE="default-src: https:")
    def test_make_middleware_configured(self):
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)

        assert handler(Mock()) is self.fake_response

        # Headers have been mutated in place (if flag enabled)
        assert self.fake_response.headers == {
            'Existing': 'something',
            'Content-Security-Policy': 'default-src: https:',
        }

########### New Test Cases #############

'''
- If GET_CUSTOM_CSPS and CSP_STATIC_ENFORCE are not set, the middleware should raise MiddlewareNotUsed.
- If GET_CUSTOM_CSPS is set, but returns None, the middleware should raise MiddlewareNotUsed.
- If GET_CUSTOM_CSPS is set, but returns an empty list, the middleware should raise MiddlewareNotUsed.
- If GET_CUSTOM_CSPS or CSP_STATIC_ENFORCE are set, the middleware should not raise MiddlewareNotUsed.
- If GET_CUSTOM_CSPS and CSP_STATIC_ENFORCE are set, GET_CUSTOM_CSPS should take precedence.
- Test that when GET_CUSTOM_CSPS is set and the current path matches one of the
regexes in the list, the value of the custom CSP is used.
- Test that when GET_CUSTOM_CSPS and CSP_STATIC_ENFORCE are set and the current path does not match any of the
regexes in the list, the value of the default CSP is used.
- Test that when GET_CUSTOM_CSPS is set and the current path does not match any of the
regexes in the list, the middleware does not append any headers.
'''