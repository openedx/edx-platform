"""
Tests for the LMS monitoring middleware
"""
import ddt
import timeit
from django.test import override_settings
from mock import call, patch, Mock
from unittest import TestCase
from unittest.mock import ANY

from lms.djangoapps.monitoring.middleware import _process_code_owner_mappings, CodeOwnerMetricMiddleware


def _mock_get_view_func_module(view_func):
    """
    Enables mocking/overriding a private function that normally gets the view_func.__module__
    because it was too difficult to mock the __module__ method.
    """
    return view_func.mock_module


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

    @override_settings(CODE_OWNER_MAPPINGS={
        'team-red': [
            'openedx.core.djangoapps.xblock',
            'lms.djangoapps.grades',
        ],
        'team-blue': [
            'common.djangoapps.xblock_django',
        ],
    })
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @patch('lms.djangoapps.monitoring.middleware._get_view_func_module', side_effect=_mock_get_view_func_module)
    @ddt.data(
        ('xbl', None),
        ('xblock_2', None),
        ('xblock', 'team-red'),
        ('openedx.core.djangoapps', None),
        ('openedx.core.djangoapps.xblock', 'team-red'),
        ('openedx.core.djangoapps.xblock.views', 'team-red'),
        ('grades', 'team-red'),
        ('lms.djangoapps.grades', 'team-red'),
        ('xblock_django', 'team-blue'),
        ('common.djangoapps.xblock_django', 'team-blue'),
    )
    @ddt.unpack
    def test_code_owner_mapping_hits_and_misses(
        self, view_func_module, expected_owner, mock_get_view_func_module, mock_set_custom_metric
    ):
        with patch('lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            mock_view_func = self._create_view_func_mock(view_func_module)
            self.middleware.process_view(None, mock_view_func, None, None)
            self._assert_code_owner_custom_metrics(
                view_func_module, mock_set_custom_metric, expected_code_owner=expected_owner
            )

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_no_mappings(self, mock_set_custom_metric):
        mock_view_func = self._create_view_func_mock('xblock')
        self.middleware.process_view(None, mock_view_func, None, None)
        mock_set_custom_metric.assert_not_called()

    @override_settings(CODE_OWNER_MAPPINGS=['invalid_setting_as_list'])
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @patch('lms.djangoapps.monitoring.middleware._get_view_func_module', side_effect=_mock_get_view_func_module)
    def test_load_config_with_invalid_dict(self, mock_get_view_func_module, mock_set_custom_metric):
        with patch('lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            mock_view_func = self._create_view_func_mock('xblock')
            self.middleware.process_view(None, mock_view_func, None, None)
            self._assert_code_owner_custom_metrics(
                'xblock', mock_set_custom_metric, has_error=True
            )

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @patch('lms.djangoapps.monitoring.middleware._get_view_func_module', side_effect=_mock_get_view_func_module)
    def test_mapping_performance(self, mock_get_view_func_module, mock_set_custom_metric):
        code_owner_mappings = {
            'team-red': []
        }
        # create a long list of mappings that are nearly identical
        for n in range(1, 200):
            path = 'openedx.core.djangoapps.{}'.format(n)
            code_owner_mappings['team-red'].append(path)
        with override_settings(CODE_OWNER_MAPPINGS=code_owner_mappings):
            with patch(
                'lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()
            ):
                # test a module that matches nearly to the end, but doesn't actually match
                mock_view_func = self._create_view_func_mock('openedx.core.djangoapps.XXX.views')
                call_iterations = 100
                time = timeit.timeit(
                    lambda: self.middleware.process_view(None, mock_view_func, None, None), number=call_iterations
                )
                average_time = time / call_iterations
                self.assertTrue(average_time < 0.0005, 'Mapping takes {}s which is too slow.'.format(average_time))
                expected_calls = []
                for n in range(1, call_iterations):
                    expected_calls.append(call('view_func_module', 'openedx.core.djangoapps.XXX.views'))
                mock_set_custom_metric.assert_has_calls(expected_calls)

    def _assert_code_owner_custom_metrics(
        self, view_func_module, mock_set_custom_metric, expected_code_owner=None, has_error=False,
    ):
        call_list = []
        call_list.append(call('view_func_module', view_func_module))
        if expected_code_owner:
            call_list.append(call('code_owner', expected_code_owner))
        if has_error:
            call_list.append(call('code_owner_mapping_error', ANY))
        mock_set_custom_metric.assert_has_calls(call_list)

    def _create_view_func_mock(self, module):
        """
        Mock view function where __module__ returns 'test_middleware'
        """
        view_func = Mock()
        view_func.mock_module = module
        return view_func
