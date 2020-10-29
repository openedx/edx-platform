"""Tests covering edX API utilities."""
# pylint: disable=missing-docstring

import json

import httpretty
import mock
from django.core.cache import cache

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.catalog.utils import create_catalog_api_client
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.core.lib.edx_api_utils import get_edx_api_data
from common.djangoapps.student.tests.factories import UserFactory

UTILITY_MODULE = 'openedx.core.lib.edx_api_utils'
TEST_API_URL = 'http://www-internal.example.com/api'


@skip_unless_lms
@httpretty.activate
class TestGetEdxApiData(CatalogIntegrationMixin, CredentialsApiConfigMixin, CacheIsolationTestCase):
    """Tests for edX API data retrieval utility."""
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetEdxApiData, self).setUp()

        self.user = UserFactory()

        httpretty.httpretty.reset()
        cache.clear()

    def _mock_catalog_api(self, responses, url=None):
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Catalog API calls.')

        url = url if url else CatalogIntegration.current().get_internal_api_url().strip('/') + '/programs/'

        httpretty.register_uri(httpretty.GET, url, responses=responses)

    def _assert_num_requests(self, count):
        """DRY helper for verifying request counts."""
        self.assertEqual(len(httpretty.httpretty.latest_requests), count)

    def test_get_unpaginated_data(self):
        """Verify that unpaginated data can be retrieved."""
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        expected_collection = ['some', 'test', 'data']
        data = {
            'next': None,
            'results': expected_collection,
        }

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(data), content_type='application/json')]
        )

        with mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__') as mock_init:
            actual_collection = get_edx_api_data(catalog_integration, 'programs', api=api)

            # Verify that the helper function didn't initialize its own client.
            self.assertFalse(mock_init.called)
            self.assertEqual(actual_collection, expected_collection)

        # Verify the API was actually hit (not the cache)
        self._assert_num_requests(1)

    def test_get_paginated_data(self):
        """Verify that paginated data can be retrieved."""
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        expected_collection = ['some', 'test', 'data']
        url = CatalogIntegration.current().get_internal_api_url().strip('/') + '/programs/?page={}'

        responses = []
        for page, record in enumerate(expected_collection, start=1):
            data = {
                'next': url.format(page + 1) if page < len(expected_collection) else None,
                'results': [record],
            }

            body = json.dumps(data)
            responses.append(
                httpretty.Response(body=body, content_type='application/json')
            )

        self._mock_catalog_api(responses)

        actual_collection = get_edx_api_data(catalog_integration, 'programs', api=api)
        self.assertEqual(actual_collection, expected_collection)

        self._assert_num_requests(len(expected_collection))

    def test_get_paginated_data_do_not_traverse_pagination(self):
        """
        Verify that pagination is not traversed if traverse_pagination=False is passed as argument.
        """
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        url = CatalogIntegration.current().get_internal_api_url().strip('/') + '/programs/?page={}'
        responses = [
            {
                'next': url.format(2),
                'results': ['some'],
            },
            {
                'next': url.format(None),
                'results': ['test'],
            },
        ]
        expected_response = responses[0]

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(body), content_type='application/json') for body in responses]
        )

        actual_collection = get_edx_api_data(catalog_integration, 'programs', api=api, traverse_pagination=False)
        self.assertEqual(actual_collection, expected_response)
        self._assert_num_requests(1)

    def test_get_specific_resource(self):
        """Verify that a specific resource can be retrieved."""
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        resource_id = 1
        url = '{api_root}/programs/{resource_id}/'.format(
            api_root=CatalogIntegration.current().get_internal_api_url().strip('/'),
            resource_id=resource_id,
        )

        expected_resource = {'key': 'value'}

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(expected_resource), content_type='application/json')],
            url=url
        )

        actual_resource = get_edx_api_data(catalog_integration, 'programs', api=api, resource_id=resource_id)
        self.assertEqual(actual_resource, expected_resource)

        self._assert_num_requests(1)

    def test_get_specific_resource_with_falsey_id(self):
        """
        Verify that a specific resource can be retrieved, and pagination parsing is
        not attempted, if the ID passed is falsey (e.g., 0). The expected resource contains
        a "results" key, as a paginatable item would have, so if the function looks for falsey
        values in the resource_id field, rather than specifically None, the function will
        return the value of that "results" key.
        """
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        resource_id = 0
        url = '{api_root}/programs/{resource_id}/'.format(
            api_root=CatalogIntegration.current().get_internal_api_url().strip('/'),
            resource_id=resource_id,
        )

        expected_resource = {'key': 'value', 'results': []}

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(expected_resource), content_type='application/json')],
            url=url
        )

        actual_resource = get_edx_api_data(catalog_integration, 'programs', api=api, resource_id=resource_id)
        self.assertEqual(actual_resource, expected_resource)

        self._assert_num_requests(1)

    def test_get_specific_fields_from_cache_response(self):
        """Verify that resource response is cached and get required fields from cached response"""
        catalog_integration = self.create_catalog_integration(cache_ttl=5)
        api = create_catalog_api_client(self.user)

        response = {'lang': 'en', 'weeks_to_complete': '5'}

        resource_id = 'course-v1:testX+testABC+1T2019'
        url = '{api_root}/course_runs/{resource_id}/'.format(
            api_root=CatalogIntegration.current().get_internal_api_url().strip('/'),
            resource_id=resource_id,
        )

        expected_resource_for_lang = {'lang': 'en'}
        expected_resource_for_weeks_to_complete = {'weeks_to_complete': '5'}

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(response), content_type='application/json')],
            url=url
        )

        cache_key = CatalogIntegration.current().CACHE_KEY

        # get response and set the cache.
        actual_resource_for_lang = get_edx_api_data(
            catalog_integration, 'course_runs', resource_id=resource_id, api=api, cache_key=cache_key, fields=['lang']
        )
        self.assertEqual(actual_resource_for_lang, expected_resource_for_lang)

        # Hit the cache
        actual_resource = get_edx_api_data(
            catalog_integration, 'course_runs', api=api, resource_id=resource_id, cache_key=cache_key,
            fields=['weeks_to_complete']
        )

        self.assertEqual(actual_resource, expected_resource_for_weeks_to_complete)

        # Verify that only one requests were made, not three.
        self._assert_num_requests(1)

    def test_cache_utilization(self):
        """Verify that when enabled, the cache is used."""
        catalog_integration = self.create_catalog_integration(cache_ttl=5)
        api = create_catalog_api_client(self.user)

        expected_collection = ['some', 'test', 'data']
        data = {
            'next': None,
            'results': expected_collection,
        }

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(data), content_type='application/json')],
        )

        resource_id = 1
        url = '{api_root}/programs/{resource_id}/'.format(
            api_root=CatalogIntegration.current().get_internal_api_url().strip('/'),
            resource_id=resource_id,
        )

        expected_resource = {'key': 'value'}

        self._mock_catalog_api(
            [httpretty.Response(body=json.dumps(expected_resource), content_type='application/json')],
            url=url
        )

        cache_key = CatalogIntegration.current().CACHE_KEY

        # Warm up the cache.
        get_edx_api_data(catalog_integration, 'programs', api=api, cache_key=cache_key)
        get_edx_api_data(catalog_integration, 'programs', api=api, resource_id=resource_id, cache_key=cache_key)

        # Hit the cache.
        actual_collection = get_edx_api_data(catalog_integration, 'programs', api=api, cache_key=cache_key)
        self.assertEqual(actual_collection, expected_collection)

        actual_resource = get_edx_api_data(
            catalog_integration, 'programs', api=api, resource_id=resource_id, cache_key=cache_key
        )
        self.assertEqual(actual_resource, expected_resource)

        # Verify that only two requests were made, not four.
        self._assert_num_requests(2)

    @mock.patch(UTILITY_MODULE + '.log.warning')
    def test_api_config_disabled(self, mock_warning):
        """Verify that no data is retrieved if the provided config model is disabled."""
        catalog_integration = self.create_catalog_integration(enabled=False)

        actual = get_edx_api_data(catalog_integration, 'programs', api=None)

        self.assertTrue(mock_warning.called)
        self.assertEqual(actual, [])

    @mock.patch(UTILITY_MODULE + '.log.exception')
    def test_data_retrieval_failure(self, mock_exception):
        """Verify that an exception is logged when data can't be retrieved."""
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        self._mock_catalog_api(
            [httpretty.Response(body='clunk', content_type='application/json', status_code=500)]
        )

        actual = get_edx_api_data(catalog_integration, 'programs', api=api)

        self.assertTrue(mock_exception.called)
        self.assertEqual(actual, [])

    @mock.patch(UTILITY_MODULE + '.log.warning')
    def test_api_config_disabled_with_id_and_not_collection(self, mock_warning):
        """Verify that no data is retrieved if the provided config model is disabled."""
        catalog_integration = self.create_catalog_integration(enabled=False)

        actual = get_edx_api_data(
            catalog_integration,
            'programs',
            api=None,
            resource_id=100,
            many=False
        )

        self.assertTrue(mock_warning.called)
        self.assertEqual(actual, {})

    @mock.patch(UTILITY_MODULE + '.log.exception')
    def test_data_retrieval_failure_with_id(self, mock_exception):
        """Verify that an exception is logged when data can't be retrieved."""
        catalog_integration = self.create_catalog_integration()
        api = create_catalog_api_client(self.user)

        self._mock_catalog_api(
            [httpretty.Response(body='clunk', content_type='application/json', status_code=500)]
        )

        actual = get_edx_api_data(
            catalog_integration,
            'programs',
            api=api,
            resource_id=100,
            many=False
        )
        self.assertTrue(mock_exception.called)
        self.assertEqual(actual, {})
