"""
Tests for the LMS monitoring middleware
"""
import ddt
from django.conf.urls import url
from django.test import override_settings, RequestFactory
from django.urls import resolve
from mock import call, patch, Mock
from rest_framework.views import APIView
from unittest import TestCase
from unittest.mock import ANY

from lms.djangoapps.monitoring.middleware import CodeOwnerMetricMiddleware
from lms.djangoapps.monitoring.tests.mock_views import MockViewTest
from lms.djangoapps.monitoring.utils import _process_code_owner_mappings


class MockMiddlewareViewTest(APIView):
    pass


urlpatterns = [
    url(r'^middleware-test/$', MockMiddlewareViewTest.as_view()),
    url(r'^test/$', MockViewTest.as_view()),
]


@ddt.ddt
class CodeOwnerMetricMiddlewareTests(TestCase):
    """
    Tests for the LMS monitoring utility functions
    """
    urls = 'lms.djangoapps.monitoring.tests.test_middleware.test_urls'

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

    _REQUEST_PATH_TO_MODULE_PATH = {
        '/middleware-test/': 'test_middleware',
        '/test/': 'lms.djangoapps.monitoring.tests.mock_views',
    }

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['lms.djangoapps.monitoring.tests.mock_views']},
        ROOT_URLCONF=__name__,
    )
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @ddt.data(
        ('/middleware-test/', None),
        ('/test/', 'team-red'),
    )
    @ddt.unpack
    def test_code_owner_mapping_hits_and_misses(
        self, request_path, expected_owner, mock_set_custom_metric
    ):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            request = RequestFactory().get(request_path)
            self.middleware(request)
            view_func, _, _ = resolve(request_path)
            expected_view_func_module = self._REQUEST_PATH_TO_MODULE_PATH[request_path]
            self._assert_code_owner_custom_metrics(
                expected_view_func_module, mock_set_custom_metric, expected_code_owner=expected_owner
            )

    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_code_owner_no_mappings(self, mock_set_custom_metric):
        request = RequestFactory().get('/test/')
        self.middleware(request)
        mock_set_custom_metric.assert_not_called()

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['lms.djangoapps.monitoring.tests.mock_views']},
    )
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_no_resolver_for_request_path(self, mock_set_custom_metric):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            request = RequestFactory().get('/bad/path/')
            self.middleware(request)
            self._assert_code_owner_custom_metrics(
                None, mock_set_custom_metric, has_error=True
            )

    @override_settings(
        CODE_OWNER_MAPPINGS=['invalid_setting_as_list'],
        ROOT_URLCONF=__name__,
    )
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    def test_load_config_with_invalid_dict(self, mock_set_custom_metric):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            request = RequestFactory().get('/test/')
            self.middleware(request)
            expected_view_func_module = self._REQUEST_PATH_TO_MODULE_PATH['/test/']
            self._assert_code_owner_custom_metrics(
                expected_view_func_module, mock_set_custom_metric, has_error=True
            )

    def _assert_code_owner_custom_metrics(
        self, view_func_module, mock_set_custom_metric, expected_code_owner=None, has_error=False,
        process_view_func=None,
    ):
        call_list = []
        if view_func_module:
            call_list.append(call('view_func_module', view_func_module))
        if expected_code_owner:
            call_list.append(call('code_owner', expected_code_owner))
        if has_error:
            call_list.append(call('code_owner_mapping_error', ANY))
        mock_set_custom_metric.assert_has_calls(call_list)
        self.assertEqual(
            len(mock_set_custom_metric.call_args_list), len(call_list),
            'Expected calls {} vs actual calls {}'.format(call_list, mock_set_custom_metric.call_args_list)
        )
