"""
Tests for the LMS monitoring middleware
"""
import ddt
import timeit
from mock import call, patch, Mock
from unittest import TestCase

from lms.djangoapps.monitoring.middleware import CodeOwnerMetricMiddleware


def mock_view_func():
    """
    Mock view function
    """


@ddt.ddt
class CodeOwnerMetricMiddlewareTests(TestCase):
    """
    Tests for the LMS monitoring utility functions
    """
    def setUp(self):
        super().setUp()
        self.mock_get_response = Mock()
        self.middleware = CodeOwnerMetricMiddleware(self.mock_get_response)

    def test_init(self):
        self.assertEqual(self.middleware.get_response, self.mock_get_response)

    def test_request_call(self):
        self.mock_get_response.return_value = 'test-response'
        request = Mock()
        self.assertEqual(self.middleware(request), 'test-response')

    @patch('lms.djangoapps.monitoring.middleware.CODE_OWNER_MAPPINGS', [('test_middleware', 'platform-arch')])
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_mapping_success(self, mock_set_custom_metric):
        self.middleware.process_view(None, mock_view_func, None, None)
        self._assert_code_owner_custom_metrics(
            mock_view_func, mock_set_custom_metric, expected_code_owner='platform-arch'
        )

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_mapping_no_mapping(self, mock_set_custom_metric):
        self.middleware.process_view(None, mock_view_func, None, None)
        self._assert_code_owner_custom_metrics(mock_view_func, mock_set_custom_metric)

    @patch('lms.djangoapps.monitoring.middleware.CODE_OWNER_MAPPINGS', ['invalid_mapping_list'])
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_mapping_error(self, mock_set_custom_metric):
        self.middleware.process_view(None, mock_view_func, None, None)
        self._assert_code_owner_custom_metrics(mock_view_func, mock_set_custom_metric, has_error=True)

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_mapping_no_mapping_performance(self, mock_set_custom_metric):
        time = timeit.timeit(lambda: self.middleware.process_view(None, mock_view_func, None, None), number=100)
        average_time = time/100
        self.assertTrue(average_time < 0.001, 'Mapping takes {}s which is too slow.'.format(average_time))

    def _assert_code_owner_custom_metrics(
        self, view_func, mock_set_custom_metric, expected_code_owner=None, has_error=False
    ):
        # default of unknown is always called in the current implementation, but this isn't required
        self.assertEqual(mock_set_custom_metric.mock_calls[0], call('view_func_module', view_func.__module__))
        if expected_code_owner:
            self.assertEqual(mock_set_custom_metric.mock_calls[1], call('code_owner', expected_code_owner))
        if has_error:
            self.assertEqual(mock_set_custom_metric.mock_calls[1].args[0], 'code_owner_mapping_error')
        time_call_index = 2 if expected_code_owner or has_error else 1
        self.assertEqual(mock_set_custom_metric.mock_calls[time_call_index].args[0], 'code_owner_mapping_time')
        self.assertTrue(mock_set_custom_metric.mock_calls[time_call_index].args[1] < 0.001)
