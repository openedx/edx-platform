"""
Tests for Content-Security-Policy middleware with custom CSP overrides.
"""

from unittest import TestCase
from unittest.mock import Mock

import ddt
import pytest
from django.test import override_settings

import openedx.core.lib.content_security_policy.middleware as csp

MiddlewareNotUsed = csp.MiddlewareNotUsed

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

    @override_settings(GET_CUSTOM_CSPS=None, CSP_STATIC_ENFORCE=None)
    def test_make_middleware_unused(self):
        with pytest.raises(MiddlewareNotUsed):
            csp.content_security_policy_middleware(lambda _: self.fake_response)

    @override_settings(GET_CUSTOM_CSPS=None, CSP_STATIC_ENFORCE="default-src: https:")
    def test_make_middleware_configured(self):
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)

        request = Mock()
        request.path = "/some-path"  # Set a valid string for the request path
        assert handler(request) is self.fake_response

        # Headers have been mutated in place (if flag enabled)
        assert self.fake_response.headers == {
            'Existing': 'something',
            'Content-Security-Policy': 'default-src: https:',
        }

    @override_settings(GET_CUSTOM_CSPS=None, CSP_STATIC_ENFORCE=None)
    def test_no_custom_csps_no_static_enforce(self):
        """Test that MiddlewareNotUsed is raised if neither GET_CUSTOM_CSPS nor CSP_STATIC_ENFORCE is set."""
        with pytest.raises(MiddlewareNotUsed):
            csp.content_security_policy_middleware(lambda _: self.fake_response)

    @override_settings(GET_CUSTOM_CSPS=lambda: None, CSP_STATIC_ENFORCE=None)
    def test_custom_csps_returns_none(self):
        """Test that MiddlewareNotUsed is raised if GET_CUSTOM_CSPS is set
        but returns None and CSP_STATIC_ENFORCE is unset."""
        with pytest.raises(MiddlewareNotUsed):
            csp.content_security_policy_middleware(lambda _: self.fake_response)

    @override_settings(GET_CUSTOM_CSPS=lambda: [], CSP_STATIC_ENFORCE=None)
    def test_custom_csps_returns_empty_list(self):
        """Test that MiddlewareNotUsed is raised if GET_CUSTOM_CSPS is set
        but returns an empty list and CSP_STATIC_ENFORCE is unset."""
        with pytest.raises(MiddlewareNotUsed):
            csp.content_security_policy_middleware(lambda _: self.fake_response)

    @override_settings(GET_CUSTOM_CSPS=lambda: [['.*', "default-src 'self'"]], CSP_STATIC_ENFORCE=None)
    def test_custom_csps_set_middleware_used(self):
        """Test that middleware is used if GET_CUSTOM_CSPS is set."""
        request = Mock()
        request.path = "/some-path"  # Set a valid string for the request path
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

    @override_settings(CSP_STATIC_ENFORCE="default-src: https:", GET_CUSTOM_CSPS=None)
    def test_static_enforce_set_middleware_used(self):
        """Test that middleware is used if CSP_STATIC_ENFORCE is set."""
        request = Mock()
        request.path = "/some-path"  # Set a valid string for the request path
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

    @override_settings(GET_CUSTOM_CSPS=lambda: [['.*', "default-src 'self'"]], CSP_STATIC_ENFORCE="default-src: https:")
    def test_custom_csps_takes_precedence(self):
        """Test that GET_CUSTOM_CSPS takes precedence over CSP_STATIC_ENFORCE."""
        request = Mock()
        request.path = "/some-path"  # Set a valid string for the request path
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

        # Headers have been mutated in place with the custom CSP
        assert self.fake_response.headers == {
            'Existing': 'something',
            'Content-Security-Policy': "default-src 'self'",
        }

    @override_settings(
        GET_CUSTOM_CSPS=lambda: [['.*/specific-path/.*', "default-src 'self'"]],
        CSP_STATIC_ENFORCE="default-src: https:"
    )
    def test_custom_csps_applied_on_specific_path(self):
        """Test that custom CSP is applied when the request path matches a regex in GET_CUSTOM_CSPS."""
        request = Mock()
        request.path = "/specific-path/resource"
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

        assert self.fake_response.headers == {
            'Existing': 'something',
            'Content-Security-Policy': "default-src 'self'",
        }

    @override_settings(
        GET_CUSTOM_CSPS=lambda: [['.*/non-matching-path/.*', "default-src 'self'"]],
        CSP_STATIC_ENFORCE="default-src: https:"
    )
    def test_default_csp_applied_when_no_custom_csp_matches(self):
        """Test that the default CSP is applied when no custom CSP regex matches the request path."""
        request = Mock()
        request.path = "/some-other-path"
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

        assert self.fake_response.headers == {
            'Existing': 'something',
            'Content-Security-Policy': 'default-src: https:',
        }

    @override_settings(
        GET_CUSTOM_CSPS=lambda: [['.*/non-matching-path/.*', "default-src 'self'"]],
        CSP_STATIC_ENFORCE=None
    )
    def test_no_csp_headers_applied_when_no_match_and_no_static_enforce(self):
        """Test that no CSP headers are applied when no custom CSP matches and no static enforce is set."""
        request = Mock()
        request.path = "/some-other-path"
        handler = csp.content_security_policy_middleware(lambda _: self.fake_response)
        assert handler(request) is self.fake_response

        assert self.fake_response.headers == {
            'Existing': 'something',
        }
