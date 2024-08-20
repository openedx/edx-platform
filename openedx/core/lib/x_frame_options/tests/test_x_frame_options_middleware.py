"""
Tests for Content-Security-Policy middleware.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.test import override_settings
from django.conf import settings

import ddt

from openedx.core.lib.x_frame_options.middleware import EdxXFrameOptionsMiddleware


@ddt.ddt
class TestEdxXFrameOptionsMiddleware(TestCase):
    """Test the actual middleware."""
    def setUp(self):
        if hasattr(settings, 'X_FRAME_OPTIONS'):
            del settings.X_FRAME_OPTIONS
        if hasattr(settings, 'X_FRAME_OPTIONS_OVERRIDES'):
            del settings.X_FRAME_OPTIONS_OVERRIDES

    @override_settings(X_FRAME_OPTIONS='SAMEORIGIN')
    @patch('openedx.core.lib.x_frame_options.middleware._validate_header_value')
    def test_x_frame_setting_must_apply_on_no_override(self, validate_header):
        """
        If the setting `X_FRAME_OPTIONS` is set but no overrides are specified,
        the `X-Frame-Options` header should be set to that setting.
        """
        validate_header.return_value = True

        request = MagicMock()
        response = MagicMock()
        response.headers = {}
        middleware = EdxXFrameOptionsMiddleware(get_response=lambda _: response)

        middleware.process_response(request, response)

        assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
        validate_header.assert_called_once_with('SAMEORIGIN')

    @override_settings(X_FRAME_OPTIONS='DENY', X_FRAME_OPTIONS_OVERRIDES=[['.*/media/scorm/.*', 'SAMEORIGIN']])
    @patch('openedx.core.lib.x_frame_options.middleware._validate_header_value')
    def test_on_override_with_valid_regex_is_sameorigin(self, validate_header):
        """
        If the URL matches one of the overrides, the header should be set to
        the correct override setting as specified in the `X_FRAME_OPTIONS_OVERRIDES` list.
        """
        validate_header.return_value = True

        request = MagicMock()
        response = MagicMock()
        response.headers = {}
        request.path = 'http://localhost:18010/media/scorm/hello/world'
        middleware = EdxXFrameOptionsMiddleware(get_response=lambda _: response)

        middleware.process_response(request, response)

        assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'

    @override_settings(X_FRAME_OPTIONS='DENY', X_FRAME_OPTIONS_OVERRIDES=[['.*/media/scorm/.*', 'SAMEORIGIN']])
    @patch('openedx.core.lib.x_frame_options.middleware._validate_header_value')
    def test_on_override_for_non_matching_urls_is_deny(self, validate_header):
        """
        If the URL does not match any of the overrides, the header should be set to
        the `X_FRAME_OPTIONS` setting.
        """
        validate_header.return_value = True

        request = MagicMock()
        response = MagicMock()
        response.headers = {}
        request.path = 'http://localhost:18010/notmedia/scorm/hello/world'
        middleware = EdxXFrameOptionsMiddleware(get_response=lambda _: response)

        middleware.process_response(request, response)

        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_x_frame_defaults_to_deny(self):
        """
        The default value of the `X-Frame-Options` header should be `DENY`.
        """
        request = MagicMock()
        response = MagicMock()
        response.headers = {}
        middleware = EdxXFrameOptionsMiddleware(get_response=lambda _: response)

        middleware.process_response(request, response)

        assert response.headers['X-Frame-Options'] == 'DENY'
