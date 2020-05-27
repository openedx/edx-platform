"""
Tests for the LMS monitoring utilities
"""

import ddt
import timeit
from django.test.utils import override_settings
from mock import patch
from unittest import TestCase

from lms.lib.monitoring import get_configured_newrelic_app_name_suffix_handler, newrelic_single_app_name_suffix_handler


def mock_test_handler(request_path):
    """
    Mock test handler function used to verify configuration, returns the provided path.
    """
    return request_path

@ddt.ddt
class MonitoringTests(TestCase):
    """
    Tests for the LMS monitoring utility functions
    """

    @ddt.data(
        ('/api-admin/api/v1/api_access_request', 'bom-squad'),
        ('/api-admin/api/v1/api_access_request/', 'bom-squad'),
        ('/api-admin/api/v1/other/', None),
    )
    @ddt.unpack
    def test_newrelic_single_app_name_suffix_handler(self, request_path, expected_suffix):
        """
        Tests the mappings from request_path to suffix.
        """
        actual_suffix = newrelic_single_app_name_suffix_handler(request_path)
        self.assertEqual(expected_suffix, actual_suffix)

    def test_unmapped_mapping_handler_speed(self):
        """
        Tests the performance of a path that is unmapped.

        Note: This time is unaccounted for in NewRelic, so we need this to be fast.
            Exactly how fast is another question, so the assertion is flexible.
        """
        unmapped_path = '/api-admin/api/v1/api_access_requests'  # Note: 's' at end makes it unmapped
        self.assertIsNone(newrelic_single_app_name_suffix_handler(unmapped_path))
        time = timeit.timeit(lambda: newrelic_single_app_name_suffix_handler(unmapped_path), number=1000)
        self.assertTrue(time < 0.005, 'Mapping is too slow for 1000 transactions.')

    @override_settings(NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER='lms.lib.tests.test_monitoring.mock_test_handler')
    def test_app_name_suffix_handler_valid_configuration(self):
        """
        Tests getting handler with a valid configuration.
        """
        returns_path_handler = get_configured_newrelic_app_name_suffix_handler()
        self.assertEqual(returns_path_handler('/test/path'), '/test/path')

    @override_settings(NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER='lms.lib.tests.invalid_mock_handler')
    @patch('lms.lib.monitoring.log')
    def test_app_name_suffix_handler_invalid_configuration(self, mock_logger):
        handler = get_configured_newrelic_app_name_suffix_handler()
        self.assertIsNone(handler)
        mock_logger.error.assert_called_with(
            (
                'Could not import NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER with value '
                'lms.lib.tests.invalid_mock_handler: Module "lms.lib.tests" does not '
                'define a "invalid_mock_handler" attribute/class.'
            )
        )

    @patch('lms.lib.monitoring.log')
    def test_app_name_suffix_handler_no_configuration(self, mock_logger):
        handler = get_configured_newrelic_app_name_suffix_handler()
        self.assertIsNone(handler)
        mock_logger.error.assert_not_called()
