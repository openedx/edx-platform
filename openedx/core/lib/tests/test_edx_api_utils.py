"""
Tests covering edX API utilities.
"""
import json

from django.core.cache import cache
from django.test.utils import override_settings
import httpretty
import mock
from nose.plugins.attrib import attr
from edx_oauth2_provider.tests.factories import ClientFactory
from openedx.core.djangoapps.catalog.tests import factories
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from provider.constants import CONFIDENTIAL
from openedx.core.djangoapps.catalog.utils import create_catalog_api_client

from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.lib.edx_api_utils import get_edx_api_data
from student.tests.factories import UserFactory


UTILITY_MODULE = 'openedx.core.lib.edx_api_utils'
TEST_API_URL = 'http://www-internal.example.com/api'
TEST_API_SIGNING_KEY = 'edx'


@attr(shard=2)
@httpretty.activate
class TestGetEdxApiDataForPrograms(ProgramsApiConfigMixin, CacheIsolationTestCase):
    """
    Tests for edX API data retrieval utility for Programs endpoints.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetEdxApiDataForPrograms, self).setUp()

        self.user = UserFactory()
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

        cache.clear()

    def _mock_programs_api(self, responses, url=None):
        """
        Helper for mocking out Programs API URLs.
        """
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = url if url else ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'

        httpretty.register_uri(httpretty.GET, url, responses=responses)

    def _assert_num_requests(self, count):
        """
        DRY helper for verifying request counts.
        """
        self.assertEqual(len(httpretty.httpretty.latest_requests), count)

    def test_get_unpaginated_data(self):
        """
        Verify that unpaginated data can be retrieved.
        """
        program_config = self.create_programs_config()

        expected_collection = ['some', 'test', 'data']
        data = {
            'next': None,
            'results': expected_collection,
        }

        self._mock_programs_api(
            [httpretty.Response(body=json.dumps(data), content_type='application/json')]
        )

        actual_collection = get_edx_api_data(program_config, self.user, 'programs')
        self.assertEqual(actual_collection, expected_collection)

        # Verify the API was actually hit (not the cache)
        self._assert_num_requests(1)

    def test_get_paginated_data(self):
        """Verify that paginated data can be retrieved."""
        program_config = self.create_programs_config()

        expected_collection = ['some', 'test', 'data']
        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/?page={}'

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

        self._mock_programs_api(responses)

        actual_collection = get_edx_api_data(program_config, self.user, 'programs')
        self.assertEqual(actual_collection, expected_collection)

        self._assert_num_requests(len(expected_collection))

    def test_get_specific_resource(self):
        """
        Verify that a specific resource can be retrieved.
        """
        program_config = self.create_programs_config()

        resource_id = 1
        url = '{api_root}/programs/{resource_id}/'.format(
            api_root=ProgramsApiConfig.current().internal_api_url.strip('/'),
            resource_id=resource_id,
        )

        expected_resource = {'key': 'value'}

        self._mock_programs_api(
            [httpretty.Response(body=json.dumps(expected_resource), content_type='application/json')],
            url=url
        )

        actual_resource = get_edx_api_data(program_config, self.user, 'programs', resource_id=resource_id)
        self.assertEqual(actual_resource, expected_resource)

        self._assert_num_requests(1)

    def test_cache_utilization(self):
        """
        Verify that when enabled, the cache is used.
        """
        program_config = self.create_programs_config(cache_ttl=5)

        expected_collection = ['some', 'test', 'data']
        data = {
            'next': None,
            'results': expected_collection,
        }

        self._mock_programs_api(
            [httpretty.Response(body=json.dumps(data), content_type='application/json')],
        )

        resource_id = 1
        url = '{api_root}/programs/{resource_id}/'.format(
            api_root=ProgramsApiConfig.current().internal_api_url.strip('/'),
            resource_id=resource_id,
        )

        expected_resource = {'key': 'value'}

        self._mock_programs_api(
            [httpretty.Response(body=json.dumps(expected_resource), content_type='application/json')],
            url=url
        )

        cache_key = ProgramsApiConfig.current().CACHE_KEY

        # Warm up the cache.
        get_edx_api_data(program_config, self.user, 'programs', cache_key=cache_key)
        get_edx_api_data(program_config, self.user, 'programs', resource_id=resource_id, cache_key=cache_key)

        # Hit the cache.
        actual_collection = get_edx_api_data(program_config, self.user, 'programs', cache_key=cache_key)
        self.assertEqual(actual_collection, expected_collection)

        actual_resource = get_edx_api_data(
            program_config, self.user, 'programs', resource_id=resource_id, cache_key=cache_key
        )
        self.assertEqual(actual_resource, expected_resource)

        # Verify that only two requests were made, not four.
        self._assert_num_requests(2)

    @mock.patch(UTILITY_MODULE + '.log.warning')
    def test_api_config_disabled(self, mock_warning):
        """
        Verify that no data is retrieved if the provided config model is disabled.
        """
        program_config = self.create_programs_config(enabled=False)

        actual = get_edx_api_data(program_config, self.user, 'programs')

        self.assertTrue(mock_warning.called)
        self.assertEqual(actual, [])

    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    @mock.patch(UTILITY_MODULE + '.log.exception')
    def test_client_initialization_failure(self, mock_exception, mock_init):
        """
        Verify that an exception is logged when the API client fails to initialize.
        """
        mock_init.side_effect = Exception

        program_config = self.create_programs_config()

        actual = get_edx_api_data(program_config, self.user, 'programs')

        self.assertTrue(mock_exception.called)
        self.assertEqual(actual, [])

    @mock.patch(UTILITY_MODULE + '.log.exception')
    def test_data_retrieval_failure(self, mock_exception):
        """
        Verify that an exception is logged when data can't be retrieved.
        """
        program_config = self.create_programs_config()

        self._mock_programs_api(
            [httpretty.Response(body='clunk', content_type='application/json', status_code=500)]
        )

        actual = get_edx_api_data(program_config, self.user, 'programs')

        self.assertTrue(mock_exception.called)
        self.assertEqual(actual, [])

    @override_settings(JWT_AUTH={'JWT_ISSUER': 'http://example.com/oauth', 'JWT_EXPIRATION': 30},
                       ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY, ECOMMERCE_API_URL=TEST_API_URL)
    def test_client_passed(self):
        """
        Verify that when API client is passed edx_rest_api_client is not used.
        """
        program_config = self.create_programs_config()
        api = ecommerce_api_client(self.user)
        with mock.patch('openedx.core.lib.edx_api_utils.EdxRestApiClient.__init__') as mock_init:
            get_edx_api_data(program_config, self.user, 'orders', api=api)
            self.assertFalse(mock_init.called)


@httpretty.activate
class TestGetEdxApiDataForCatalog(CatalogIntegrationMixin, CacheIsolationTestCase):
    """
    Tests for edX API data retrieval utility for Catalog endpoints.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetEdxApiDataForCatalog, self).setUp()
        self.user = UserFactory()
        self.catalog_integration = self.create_catalog_integration(
            internal_api_url="http://catalog.example.com:443/api/v1",
            cache_ttl=1,
        )

    def _create_course_run_data(self, count):
        """
        Create course run data.
        """
        course_runs = [factories.CourseRun() for __ in range(count)]
        course_key_strings = [course_run["key"] for course_run in course_runs]
        return course_runs, course_key_strings

    def test_get_unpaginated_data(self):
        """
        Verify that unpaginated data can be retrieved.
        """
        course_runs, course_key_strings = self._create_course_run_data(5)
        self.register_catalog_course_run_response(course_key_strings, course_runs)
        api = create_catalog_api_client(self.user, self.catalog_integration)

        actual_collection = get_edx_api_data(
            self.catalog_integration,
            self.user,
            'course_runs',
            api=api,
            querystring={'keys': ",".join(course_key_strings), 'exclude_utm': 1},
        )
        self.assertEqual(len(actual_collection), 5)
        self.assertEqual(actual_collection, course_runs)

    def test_get_paginated_data(self):
        """
        Verify that limit-offset based DRF paginated data can be retrieved.
        """
        course_runs, course_key_strings = self._create_course_run_data(22)
        self.register_catalog_course_run_response(course_key_strings[:20], course_runs[:20])
        self.register_catalog_course_run_response(course_key_strings[20:], course_runs[20:], 2)
        api = create_catalog_api_client(self.user, self.catalog_integration)

        actual_collection = get_edx_api_data(
            self.catalog_integration,
            self.user,
            'course_runs',
            api=api,
            querystring={'keys': ",".join(course_key_strings), 'exclude_utm': 1},
        )
        self.assertEqual(len(actual_collection), 22)
        self.assertEqual(actual_collection, course_runs[20:] + course_runs[:20])
