"""
Tests for the LMS monitoring middleware
"""
import ddt
from django.conf.urls import url
from django.test import override_settings, RequestFactory
from edx_django_utils.cache import RequestCache
from mock import call, patch, Mock
from rest_framework.views import APIView
from unittest import TestCase
from unittest.mock import ANY

from lms.djangoapps.monitoring.middleware import CodeOwnerMetricMiddleware
from lms.djangoapps.monitoring.tests.mock_views import MockViewAnotherTest, MockViewTest
from lms.djangoapps.monitoring.utils import _process_code_owner_mappings


class MockMiddlewareViewTest(APIView):
    pass


urlpatterns = [
    url(r'^middleware-test/$', MockMiddlewareViewTest.as_view()),
    url(r'^test/$', MockViewTest.as_view()),
    url(r'^another-test/$', MockViewAnotherTest.as_view()),
]

@ddt.ddt
class CodeOwnerMetricMiddlewareTests(TestCase):
    """
    Tests for the LMS monitoring utility functions
    """
    urls = 'lms.djangoapps.monitoring.tests.test_middleware.test_urls'

    def setUp(self):
        super().setUp()
        RequestCache.clear_all_namespaces()
        self.mock_get_response = Mock()
        self.middleware = CodeOwnerMetricMiddleware(self.mock_get_response)

    def test_init(self):
        self.assertEqual(self.middleware.get_response, self.mock_get_response)

    def test_request_call(self):
        self.mock_get_response.return_value = 'test-response'
        request = Mock()
        self.assertEqual(self.middleware(request), 'test-response')

    @override_settings(
        CODE_OWNER_MAPPINGS={
            'team-red': ['openedx.core.djangoapps.xblock'],
            'team-blue': ['common.djangoapps.xblock_django'],
        },
        ROOT_URLCONF=__name__
    )
    @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    @ddt.data(
        ('/test/', 'lms.djangoapps.monitoring.tests.mock_views', 'team-red'),
    )
    @ddt.unpack
    def test_process_request_code_owner_mapping_hits_and_misses(
        self, request_path, expected_module, expected_owner, mock_set_custom_metric
    ):
        with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
            request = RequestFactory().get(request_path)
            self.middleware(request)
            self._assert_code_owner_custom_metrics(
                expected_module, mock_set_custom_metric, expected_code_owner=expected_owner
            )

    # @override_settings(CODE_OWNER_MAPPINGS={
    #     'team-red': [
    #         'openedx.core.djangoapps.xblock',
    #     ],
    #     'team-blue': [
    #         'common.djangoapps.xblock_django',
    #     ],
    # })
    # @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    # @ddt.data(
    #     ('xblock', 'team-red'),
    #     ('openedx.core.djangoapps', None),
    #     ('openedx.core.djangoapps.xblock.views', 'team-red'),
    #     ('xblock_django', 'team-blue'),
    #     ('common.djangoapps.xblock_django', 'team-blue'),
    # )
    # @ddt.unpack
    # def test_code_owner_mapping_hits_and_misses(
    #     self, view_func_module, expected_owner, mock_set_custom_metric
    # ):
    #     with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
    #         mock_view_func = MockViewWithMockModule(view_func_module)
    #         self.middleware.process_view(None, mock_view_func, None, None)
    #         self._assert_code_owner_custom_metrics(
    #             view_func_module, mock_set_custom_metric, expected_code_owner=expected_owner
    #         )
    #
    # @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    # def test_code_owner_no_mappings(self, mock_set_custom_metric):
    #     mock_view_func = MockViewWithMockModule('xblock')
    #     self.middleware.process_view(None, mock_view_func, None, None)
    #     mock_set_custom_metric.assert_not_called()
    #
    # @override_settings(CODE_OWNER_MAPPINGS=['invalid_setting_as_list'])
    # @patch('lms.djangoapps.monitoring.middleware.set_custom_metric')
    # def test_load_config_with_invalid_dict(self, mock_set_custom_metric):
    #     with patch('lms.djangoapps.monitoring.utils._PATH_TO_CODE_OWNER_MAPPINGS', _process_code_owner_mappings()):
    #         mock_view_func = MockViewWithMockModule('xblock')
    #         self.middleware.process_view(None, mock_view_func, None, None)
    #         self._assert_code_owner_custom_metrics(
    #             'xblock', mock_set_custom_metric, has_error=True
    #         )

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
