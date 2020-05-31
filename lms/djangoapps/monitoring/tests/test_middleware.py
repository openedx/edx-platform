"""
Tests for the LMS monitoring middleware
"""
import ddt
import timeit
from django.test import override_settings
from mock import call, patch, Mock
from unittest import TestCase
from unittest.mock import ANY

from lms.djangoapps.monitoring.middleware import _load_path_to_code_owner_mappings, CodeOwnerMetricMiddleware


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
            'xblock',
        ],
        'team-blue': [
            'xblock_django',
        ],
        'team-black': [
            'openedx.core.djangoapps.xblock',
        ],
    })
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @patch('lms.djangoapps.monitoring.middleware._get_view_func_module', side_effect=_mock_get_view_func_module)
    @ddt.data(
        ('xbl', None),
        ('xblock_2', None),
        ('xblock', 'team-red'),
        ('xblock_django', 'team-blue'),
        ('openedx.core.djangoapps', None),
        ('openedx.core.djangoapps.xblock', 'team-black'),
        ('openedx.core.djangoapps.xblock.views', 'team-black'),
    )
    @ddt.unpack
    def test_code_owner_mapping_hits_and_misses(
        self, view_func_module, expected_owner, mock_get_view_func_module, mock_set_custom_metric
    ):
        path_to_code_owner_mappings, _ = _load_path_to_code_owner_mappings()
        with patch('lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS', path_to_code_owner_mappings):
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
    def test_load_config_with_invalid_dict(self, mock_set_custom_metric):
        path_to_code_owner_mappings, config_load_errors = _load_path_to_code_owner_mappings()
        with patch(
            'lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS',
            path_to_code_owner_mappings
        ):
            with patch(
                'lms.djangoapps.monitoring.middleware._CODE_OWNER_MAPPINGS_CONFIG_LOAD_ERRORS',
                config_load_errors
            ):
                mock_view_func = self._create_view_func_mock('xblock')
                self.middleware.process_view(None, mock_view_func, None, None)
                mock_set_custom_metric.assert_called_once()
                self.assertEqual(mock_set_custom_metric.mock_calls[0].args[0], 'code_owner_mapping_config_load_errors')
                errors_arg = mock_set_custom_metric.mock_calls[0].args[1]
                self.assertTrue(any('should be a dict' in error for error in errors_arg))

    @override_settings(CODE_OWNER_MAPPINGS=['invalid_mapping_list'])
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_load_config_with_invalid_settings(self, mock_set_custom_metric):
        assert False, 'TODO: Add DDT for different settings.'
        path_to_code_owner_mappings, config_load_errors = _load_path_to_code_owner_mappings()
        with patch(
            'lms.djangoapps.monitoring.middleware._PATH_TO_CODE_OWNER_MAPPINGS',
            path_to_code_owner_mappings
        ):
            with patch(
                'lms.djangoapps.monitoring.middleware._CODE_OWNER_MAPPINGS_CONFIG_LOAD_ERRORS',
                config_load_errors
            ):
                mock_view_func = self._create_view_func_mock('xblock')
                self.middleware.process_view(None, mock_view_func, None, None)
                self._assert_code_owner_custom_metrics(
                    'xblock', mock_set_custom_metric, has_error=True, load_error='should be a dict'
                )

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @patch('lms.djangoapps.monitoring.middleware._get_view_func_module', side_effect=_mock_get_view_func_module)
    def test_mapping_performance(self, mock_get_view_func_module, mock_set_custom_metric):
        code_owner_mappings = []
        # create a long list of mappings that are nearly identical
        for n in range(1, 200):
            path = 'openedx.core.djangoapps.{}'.format(n)
            code_owner_mappings.append([path, 'team-red'])
        # test a module that matches nearly to the end, but doesn't actually match
        mock_view_func = self._create_view_func_mock('openedx.core.djangoapps.XXX.views')
        with override_settings(CODE_OWNER_MAPPINGS=code_owner_mappings):
            time = timeit.timeit(lambda: self.middleware.process_view(None, mock_view_func, None, None), number=100)
        average_time = time / 100
        self.assertTrue(average_time < 0.005, 'Mapping takes {}s which is too slow.'.format(average_time))
        self._assert_code_owner_custom_metrics(mock_view_func, mock_set_custom_metric)

    def _assert_code_owner_custom_metrics(
        self, view_func_module, mock_set_custom_metric, expected_code_owner=None, has_error=False, load_error=None
    ):
        call_list = []
        if load_error:
            call_list.append(call('code_owner_mapping_config_load_errors', ANY))
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
