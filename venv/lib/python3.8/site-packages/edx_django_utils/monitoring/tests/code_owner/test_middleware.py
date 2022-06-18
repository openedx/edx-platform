"""
Tests for the code_owner monitoring middleware
"""
from unittest import TestCase
from unittest.mock import ANY, MagicMock, Mock, call, patch

import ddt
from django.test import RequestFactory, override_settings
from django.urls import re_path
from django.views.generic import View

from edx_django_utils.monitoring import CodeOwnerMonitoringMiddleware
from edx_django_utils.monitoring.internal.code_owner.utils import clear_cached_mappings

from .mock_views import MockViewTest


class MockMiddlewareViewTest(View):
    pass


urlpatterns = [
    re_path(r'^middleware-test/$', MockMiddlewareViewTest.as_view()),
    re_path(r'^test/$', MockViewTest.as_view()),
]

SET_CUSTOM_ATTRIBUTE_MOCK = MagicMock()


# Enables the same mock to be used from different modules, using
#   patch with new_callable=get_set_custom_attribute_mock
def get_set_custom_attribute_mock():
    return SET_CUSTOM_ATTRIBUTE_MOCK


@ddt.ddt
class CodeOwnerMetricMiddlewareTests(TestCase):
    """
    Tests for the code_owner monitoring utility functions
    """
    urls = 'lms.djangoapps.monitoring.tests.test_middleware.test_urls'

    def setUp(self):
        super().setUp()
        clear_cached_mappings()
        SET_CUSTOM_ATTRIBUTE_MOCK.reset_mock()
        self.mock_get_response = Mock()
        self.middleware = CodeOwnerMonitoringMiddleware(self.mock_get_response)

    def test_init(self):
        self.assertEqual(self.middleware.get_response, self.mock_get_response)

    def test_request_call(self):
        self.mock_get_response.return_value = 'test-response'
        request = Mock()
        self.assertEqual(self.middleware(request), 'test-response')

    _REQUEST_PATH_TO_MODULE_PATH = {
        '/middleware-test/': 'edx_django_utils.monitoring.tests.code_owner.test_middleware',
        '/test/': 'edx_django_utils.monitoring.tests.code_owner.mock_views',
    }

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['edx_django_utils.monitoring.tests.code_owner.mock_views']},
        CODE_OWNER_THEMES={'team': ['team-red']},
        ROOT_URLCONF=__name__,
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @ddt.data(
        ('/middleware-test/', None),
        ('/test/', 'team-red'),
    )
    @ddt.unpack
    def test_code_owner_path_mapping_hits_and_misses(
        self, request_path, expected_owner, mock_set_custom_attribute, _
    ):
        request = RequestFactory().get(request_path)
        self.middleware(request)
        expected_path_module = self._REQUEST_PATH_TO_MODULE_PATH[request_path]
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=expected_path_module,
            check_theme_and_squad=True
        )

        mock_set_custom_attribute.reset_mock()
        self.middleware.process_exception(request, None)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=expected_path_module,
            check_theme_and_squad=True
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={
            'team-red': ['edx_django_utils.monitoring.tests.code_owner.mock_views'],
            'team-blue': ['*'],
        },
        ROOT_URLCONF=__name__,
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @ddt.data(
        ('/middleware-test/', 'team-blue'),
        ('/test/', 'team-red'),
    )
    @ddt.unpack
    def test_code_owner_path_mapping_with_catch_all(
        self, request_path, expected_owner, mock_set_custom_attribute, _
    ):
        request = RequestFactory().get(request_path)
        self.middleware(request)
        expected_path_module = self._REQUEST_PATH_TO_MODULE_PATH[request_path]
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=expected_path_module
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['edx_django_utils.monitoring.tests.code_owner.mock_views']},
        ROOT_URLCONF=__name__,
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch('newrelic.agent')
    @ddt.data(
        (
            'edx_django_utils.monitoring.tests.code_owner.test_middleware',
            'edx_django_utils.monitoring.tests.code_owner.test_middleware:MockMiddlewareViewTest',
            None
        ),
        (
            'edx_django_utils.monitoring.tests.code_owner.mock_views',
            'edx_django_utils.monitoring.tests.code_owner.mock_views:MockViewTest',
            'team-red'
        ),
    )
    @ddt.unpack
    def test_code_owner_transaction_mapping_hits_and_misses(
        self, path_module, transaction_name, expected_owner, mock_newrelic_agent, mock_set_custom_attribute, _
    ):
        mock_newrelic_agent.current_transaction().name = transaction_name
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=path_module,
            transaction_name=transaction_name
        )

        mock_set_custom_attribute.reset_mock()
        self.middleware.process_exception(request, None)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=path_module,
            transaction_name=transaction_name
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={
            'team-red': ['edx_django_utils.monitoring.tests.code_owner.mock_views'],
            'team-blue': ['*'],
        },
        ROOT_URLCONF=__name__,
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch('newrelic.agent')
    @ddt.data(
        (
            'edx_django_utils.monitoring.tests.code_owner.test_middleware',
            'edx_django_utils.monitoring.tests.code_owner.test_middleware:MockMiddlewareViewTest',
            'team-blue'
        ),
        (
            'edx_django_utils.monitoring.tests.code_owner.mock_views',
            'edx_django_utils.monitoring.tests.code_owner.mock_views:MockViewTest',
            'team-red'
        ),
    )
    @ddt.unpack
    def test_code_owner_transaction_mapping_with_catch_all(
        self, path_module, transaction_name, expected_owner, mock_newrelic_agent, mock_set_custom_attribute, _
    ):
        mock_newrelic_agent.current_transaction().name = transaction_name
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, expected_code_owner=expected_owner, path_module=path_module,
            transaction_name=transaction_name
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['edx_django_utils.monitoring.tests.code_owner.mock_views']},
        ROOT_URLCONF=__name__,
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch('newrelic.agent')
    def test_code_owner_transaction_mapping_error(self, mock_newrelic_agent, mock_set_custom_attribute, _):
        mock_newrelic_agent.current_transaction = Mock(side_effect=Exception('forced exception'))
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, has_path_error=True, has_transaction_error=True
        )

    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_code_owner_no_mappings(self, mock_set_custom_attribute):
        request = RequestFactory().get('/test/')
        self.middleware(request)
        mock_set_custom_attribute.assert_not_called()

    @patch('edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute')
    def test_code_owner_transaction_no_mappings(self, mock_set_custom_attribute):
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        mock_set_custom_attribute.assert_not_called()

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['lms.djangoapps.monitoring.tests.mock_views']},
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    def test_no_resolver_for_path_and_no_transaction(self, mock_set_custom_attribute, _):
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, has_path_error=True, has_transaction_error=True
        )

    @override_settings(
        CODE_OWNER_MAPPINGS={'team-red': ['*']},
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.utils.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    @patch(
        'edx_django_utils.monitoring.internal.code_owner.middleware.set_custom_attribute',
        new_callable=get_set_custom_attribute_mock
    )
    def test_catch_all_with_errors(self, mock_set_custom_attribute, _):
        request = RequestFactory().get('/bad/path/')
        self.middleware(request)
        self._assert_code_owner_custom_attributes(
            mock_set_custom_attribute, has_path_error=True, has_transaction_error=True, expected_code_owner='team-red'
        )

    @override_settings(
        CODE_OWNER_MAPPINGS=['invalid_setting_as_list'],
        ROOT_URLCONF=__name__,
    )
    def test_load_config_with_invalid_dict(self):
        request = RequestFactory().get('/test/')
        with self.assertRaises(TypeError):
            self.middleware(request)

    def _assert_code_owner_custom_attributes(self, mock_set_custom_attribute, expected_code_owner=None,
                                             path_module=None, has_path_error=False,
                                             transaction_name=None, has_transaction_error=False,
                                             check_theme_and_squad=False):
        """ Performs a set of assertions around having set the proper custom attributes. """
        call_list = []
        if expected_code_owner:
            call_list.append(call('code_owner', expected_code_owner))
            if check_theme_and_squad:
                call_list.append(call('code_owner_theme', expected_code_owner.split('-')[0]))
                call_list.append(call('code_owner_squad', expected_code_owner.split('-')[1]))
        if path_module:
            call_list.append(call('code_owner_module', path_module))
        if has_path_error:
            call_list.append(call('code_owner_path_error', ANY))
        if transaction_name:
            call_list.append(call('code_owner_transaction_name', transaction_name))
        if has_transaction_error:
            call_list.append(call('code_owner_transaction_error', ANY))
        # TODO: Remove this list filtering once the ``deprecated_broad_except_XXX`` custom attributes have been removed.
        actual_filtered_call_list = [
            mock_call
            for mock_call in mock_set_custom_attribute.call_args_list
            if not mock_call[0][0].startswith('deprecated_')
        ]
        mock_set_custom_attribute.assert_has_calls(call_list, any_order=True)
        self.assertEqual(
            len(actual_filtered_call_list), len(call_list),
            f'Expected calls {call_list} vs actual calls {actual_filtered_call_list}'
        )
