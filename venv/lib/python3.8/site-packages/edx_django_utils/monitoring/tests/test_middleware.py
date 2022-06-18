"""
Tests monitoring middleware.

Note: CachedCustomMonitoringMiddleware is tested in ``test_custom_monitoring.py``.
"""
import re
from unittest.mock import Mock, call, patch

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from waffle.testutils import override_switch

from edx_django_utils.cache import RequestCache
from edx_django_utils.monitoring import (
    CookieMonitoringMiddleware,
    DeploymentMonitoringMiddleware,
    MonitoringMemoryMiddleware
)


class TestMonitoringMemoryMiddleware(TestCase):
    """
    Tests for MonitoringMemoryMiddleware
    """
    @override_switch('edx_django_utils.monitoring.enable_memory_middleware', False)
    @patch('edx_django_utils.monitoring.internal.middleware.log')
    def test_memory_monitoring_when_disabled(self, mock_logger):
        MonitoringMemoryMiddleware().process_response(
            'fake request',
            'fake response',
        )
        mock_logger.info.assert_not_called()

    @override_switch('edx_django_utils.monitoring.enable_memory_middleware', True)
    @patch('edx_django_utils.monitoring.internal.middleware.log')
    def test_memory_monitoring_when_enabled(self, mock_logger):
        request = RequestFactory().get('/')
        MonitoringMemoryMiddleware().process_response(
            request,
            'fake response',
        )
        mock_logger.info.assert_called()


class TestDeploymentMonitoringMiddleware(TestCase):
    """
    Test the DeploymentMonitoringMiddleware functionalities
    """
    version_pattern = r'\d+(\.\d+){2}'

    def setUp(self):
        super().setUp()
        RequestCache.clear_all_namespaces()

    def _test_key_value_pair(self, function_call, key):
        """
        Asserts the function call key and value with the provided key and the default version_pattern
        """
        attribute_key, attribute_value = function_call[0]
        assert attribute_key == key
        assert re.match(re.compile(self.version_pattern), attribute_value)

    @patch('newrelic.agent')
    def test_record_python_and_django_version(self, mock_newrelic_agent):
        """
        Test that the DeploymentMonitoringMiddleware records the correct Python and Django versions
        """
        middleware = DeploymentMonitoringMiddleware(Mock())
        middleware(Mock())

        parameter_calls_count = mock_newrelic_agent.add_custom_parameter.call_count
        assert parameter_calls_count == 2

        function_calls = mock_newrelic_agent.add_custom_parameter.call_args_list
        self._test_key_value_pair(function_calls[0], 'python_version')
        self._test_key_value_pair(function_calls[1], 'django_version')


@ddt.ddt
class CookieMonitoringMiddlewareTestCase(TestCase):
    """
    Tests for CookieMonitoringMiddleware.
    """
    def setUp(self):
        super().setUp()
        self.mock_response = Mock()

    @patch('edx_django_utils.monitoring.internal.middleware.log', autospec=True)
    @patch("edx_django_utils.monitoring.internal.middleware._set_custom_attribute")
    @ddt.data(
        (None, None),  # logging threshold not defined
        (5, None),  # logging threshold too high
        (5, 9999999999999999999),  # logging threshold too high, and random sampling impossibly unlikely
    )
    @ddt.unpack
    def test_cookie_monitoring_with_no_logging(
        self, logging_threshold, sampling_request_count, mock_set_custom_attribute, mock_logger
    ):
        expected_response = self.mock_response
        middleware = CookieMonitoringMiddleware(lambda request: expected_response)
        cookies_dict = {'a': 'y'}

        with override_settings(COOKIE_HEADER_SIZE_LOGGING_THRESHOLD=logging_threshold):
            with override_settings(COOKIE_SAMPLING_REQUEST_COUNT=sampling_request_count):
                actual_response = middleware(self.get_mock_request(cookies_dict))

        assert actual_response == expected_response
        # expect monitoring of header size for all requests
        mock_set_custom_attribute.assert_called_once_with('cookies.header.size', 3)
        # cookie logging was not enabled, so nothing should be logged
        mock_logger.info.assert_not_called()
        mock_logger.exception.assert_not_called()

    @override_settings(COOKIE_HEADER_SIZE_LOGGING_THRESHOLD=None)
    @override_settings(COOKIE_SAMPLING_REQUEST_COUNT=None)
    @patch("edx_django_utils.monitoring.internal.middleware._set_custom_attribute")
    @ddt.data(
        # A corrupt cookie header contains "Cookie: ".
        ('corruptCookie: normal-cookie=value', 1, 1),
        ('corrupt1Cookie: normal-cookie1=value1;corrupt2Cookie: normal-cookie2=value2', 2, 2),
        ('corrupt=Cookie: value', 1, 0),
    )
    @ddt.unpack
    def test_cookie_header_corrupt_monitoring(
        self, corrupt_cookie_header, expected_corrupt_count, expected_corrupt_key_count, mock_set_custom_attribute
    ):
        middleware = CookieMonitoringMiddleware(self.mock_response)
        request = RequestFactory().request()
        request.META['HTTP_COOKIE'] = corrupt_cookie_header

        middleware(request)

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.header.size', len(request.META['HTTP_COOKIE'])),
            call('cookies.header.corrupt_count', expected_corrupt_count),
            call('cookies.header.corrupt_key_count', expected_corrupt_key_count),
        ])

    @override_settings(COOKIE_HEADER_SIZE_LOGGING_THRESHOLD=1)
    @patch('edx_django_utils.monitoring.internal.middleware.log', autospec=True)
    @patch("edx_django_utils.monitoring.internal.middleware._set_custom_attribute")
    def test_log_cookie_with_threshold_met(self, mock_set_custom_attribute, mock_logger):
        middleware = CookieMonitoringMiddleware(self.mock_response)
        cookies_dict = {
            "a": "yy",
            "b": "xxx",
            "c": "z",
        }

        middleware(self.get_mock_request(cookies_dict))

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.header.size', 16),
            call('cookies.header.size.computed', 16)
        ])
        mock_logger.info.assert_called_once_with(
            "Large (>= 1) cookie header detected. BEGIN-COOKIE-SIZES(total=16) b: 3, a: 2, c: 1 END-COOKIE-SIZES"
        )
        mock_logger.exception.assert_not_called()

    @override_settings(COOKIE_HEADER_SIZE_LOGGING_THRESHOLD=9999)
    @override_settings(COOKIE_SAMPLING_REQUEST_COUNT=1)
    @patch('edx_django_utils.monitoring.internal.middleware.log', autospec=True)
    @patch("edx_django_utils.monitoring.internal.middleware._set_custom_attribute")
    def test_log_cookie_with_sampling(self, mock_set_custom_attribute, mock_logger):
        middleware = CookieMonitoringMiddleware(self.mock_response)
        cookies_dict = {
            "a": "yy",
            "b": "xxx",
            "c": "z",
        }

        middleware(self.get_mock_request(cookies_dict))

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.header.size', 16),
            call('cookies.header.size.computed', 16)
        ])
        mock_logger.info.assert_called_once_with(
            "Sampled small (< 9999) cookie header. BEGIN-COOKIE-SIZES(total=16) b: 3, a: 2, c: 1 END-COOKIE-SIZES"
        )
        mock_logger.exception.assert_not_called()

    @override_settings(COOKIE_HEADER_SIZE_LOGGING_THRESHOLD=9999)
    @override_settings(COOKIE_SAMPLING_REQUEST_COUNT=1)
    @patch('edx_django_utils.monitoring.internal.middleware.log', autospec=True)
    @patch("edx_django_utils.monitoring.internal.middleware._set_custom_attribute")
    def test_empty_cookie_header_skips_sampling(self, mock_set_custom_attribute, mock_logger):
        middleware = CookieMonitoringMiddleware(self.mock_response)
        cookies_dict = {}

        middleware(self.get_mock_request(cookies_dict))

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.header.size', 0),
        ])
        mock_logger.info.assert_not_called()
        mock_logger.exception.assert_not_called()

    @patch('edx_django_utils.monitoring.internal.middleware.log', autospec=True)
    def test_cookie_monitoring_unknown_exception(self, mock_logger):
        middleware = CookieMonitoringMiddleware(self.mock_response)
        cookies_dict = {'a': 'y'}
        mock_request = self.get_mock_request(cookies_dict)
        mock_request.META = Mock()
        mock_request.META.side_effect = Exception("Some exception")

        middleware(mock_request)

        mock_logger.exception.assert_called_once_with("Unexpected error logging and monitoring cookies.")

    def get_mock_request(self, cookies_dict):
        """
        Return mock request with the provided cookies in the header.
        """
        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value
        return factory.request()
