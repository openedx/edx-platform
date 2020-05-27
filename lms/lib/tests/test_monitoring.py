"""
Tests for the LMS monitoring utilities
"""
import ddt
from django.test.utils import override_settings
from mock import call, patch
from unittest import TestCase

from lms.lib.monitoring import get_configured_newrelic_app_name_suffix_handler, set_new_relic_app_name


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

    @patch('lms.lib.monitoring.newrelic_app_name_suffix_handler', return_value='test-suffix')
    @patch('lms.lib.monitoring.set_custom_metric')
    def test_set_new_relic_app_name_success(self, mock_set_custom_metric, mock_handler):
        mock_environ = {
            'PATH_INFO': '/test/path',
            'newrelic.app_name': 'test-app',
        }
        expected_app_name = 'test-app-test-suffix'
        set_new_relic_app_name(mock_environ)
        self._assert_app_name_and_custom_metrics(expected_app_name, mock_environ, mock_set_custom_metric)

    @patch('lms.lib.monitoring.newrelic_app_name_suffix_handler', return_value=None)
    @patch('lms.lib.monitoring.set_custom_metric')
    def test_set_new_relic_app_name_no_mapping(self, mock_set_custom_metric, mock_handler):
        mock_environ = {
            'PATH_INFO': '/test/path',
            'newrelic.app_name': 'test-app',
        }
        expected_app_name = 'test-app'
        set_new_relic_app_name(mock_environ)
        self._assert_app_name_and_custom_metrics(expected_app_name, mock_environ, mock_set_custom_metric)

    @patch('lms.lib.monitoring.newrelic_app_name_suffix_handler', return_value='test-suffix')
    @patch('lms.lib.monitoring.set_custom_metric')
    def test_set_new_relic_app_name_no_path(self, mock_set_custom_metric, mock_handler):
        mock_environ = {
            'newrelic.app_name': 'test-app',
        }
        expected_app_name = 'test-app'
        set_new_relic_app_name(mock_environ)
        self.assertEqual(mock_environ['newrelic.app_name'], expected_app_name)
        mock_set_custom_metric.assert_not_called()

    @patch('lms.lib.monitoring.newrelic_app_name_suffix_handler', return_value='test-suffix')
    @patch('lms.lib.monitoring.set_custom_metric')
    def test_set_new_relic_app_name_no_app_name(self, mock_set_custom_metric, mock_handler):
        mock_environ = {
            'PATH_INFO': '/test/path',
        }
        set_new_relic_app_name(mock_environ)
        self.assertTrue('newrelic.app_name' not in mock_environ)
        mock_set_custom_metric.assert_not_called()

    @patch('lms.lib.monitoring.newrelic_app_name_suffix_handler')
    @patch('lms.lib.monitoring.set_custom_metric')
    def test_set_new_relic_app_name_no_mapping(self, mock_set_custom_metric, mock_handler):
        expected_exception = Exception('Oops!')
        mock_handler.side_effect = expected_exception
        mock_environ = {
            'PATH_INFO': '/test/path',
            'newrelic.app_name': 'test-app',
        }
        expected_app_name = 'test-app'
        set_new_relic_app_name(mock_environ)
        self.assertEqual(mock_environ['newrelic.app_name'], expected_app_name)
        self.assertEqual(mock_set_custom_metric.mock_calls[0], call('suffix_mapping_error', expected_exception))

    def _assert_app_name_and_custom_metrics(self, expected_app_name, mock_environ, mock_set_custom_metric):
        self.assertEqual(mock_environ['newrelic.app_name'], expected_app_name)
        self.assertEqual(mock_set_custom_metric.mock_calls[0], call('updated_app_name', expected_app_name))
        self.assertEqual(mock_set_custom_metric.mock_calls[1].args[0], 'suffix_mapping_time')
        self.assertTrue(mock_set_custom_metric.mock_calls[1].args[1] < 0.001)
