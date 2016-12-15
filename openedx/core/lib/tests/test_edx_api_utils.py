"""Tests covering Api utils."""

from django.core.cache import cache
from django.test import TestCase
import httpretty
import mock
from oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL
from testfixtures import LogCapture

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin, CredentialsDataMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.lib.edx_api_utils import get_edx_api_data
from student.tests.factories import UserFactory


LOGGER_NAME = 'openedx.core.lib.edx_api_utils'


class TestApiDataRetrieval(CredentialsApiConfigMixin, CredentialsDataMixin, ProgramsApiConfigMixin, ProgramsDataMixin,
                           TestCase):
    """Test utility for API data retrieval."""
    def setUp(self):
        super(TestApiDataRetrieval, self).setUp()
        ClientFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.user = UserFactory()

        cache.clear()

    @httpretty.activate
    def test_get_edx_api_data_programs(self):
        """Verify programs data can be retrieved using get_edx_api_data."""
        program_config = self.create_programs_config()
        self.mock_programs_api()

        actual = get_edx_api_data(program_config, self.user, 'programs')
        self.assertEqual(
            actual,
            self.PROGRAMS_API_RESPONSE['results']
        )

        # Verify the API was actually hit (not the cache).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    def test_get_edx_api_data_disable_config(self):
        """Verify no data is retrieved if configuration is disabled."""
        program_config = self.create_programs_config(enabled=False)

        actual = get_edx_api_data(program_config, self.user, 'programs')
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_edx_api_data_cache(self):
        """Verify that when enabled, the cache is used."""
        program_config = self.create_programs_config(cache_ttl=1)
        self.mock_programs_api()

        # Warm up the cache.
        get_edx_api_data(program_config, self.user, 'programs', cache_key='test.key')

        # Hit the cache.
        get_edx_api_data(program_config, self.user, 'programs', cache_key='test.key')

        # Verify only one request was made.
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_edx_api_data_client_initialization_failure(self, mock_init):
        """Verify no data is retrieved and exception logged when API client
        fails to initialize.
        """
        program_config = self.create_programs_config()
        mock_init.side_effect = Exception

        with LogCapture(LOGGER_NAME) as logger:
            actual = get_edx_api_data(program_config, self.user, 'programs')
            logger.check(
                (LOGGER_NAME, 'ERROR', u'Failed to initialize the programs API client.')
            )
            self.assertEqual(actual, [])
            self.assertTrue(mock_init.called)

    @httpretty.activate
    def test_get_edx_api_data_retrieval_failure(self):
        """Verify exception is logged when data can't be retrieved from API."""
        program_config = self.create_programs_config()
        self.mock_programs_api(status_code=500)
        with LogCapture(LOGGER_NAME) as logger:
            actual = get_edx_api_data(program_config, self.user, 'programs')
            logger.check(
                (LOGGER_NAME, 'ERROR', u'Failed to retrieve data from the programs API.')
            )
            self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_edx_api_data_multiple_page(self):
        """Verify that all data is retrieve for multiple page response."""
        credentials_config = self.create_credentials_config()
        self.mock_credentials_api(self.user, is_next_page=True)
        querystring = {'username': self.user.username}

        actual = get_edx_api_data(credentials_config, self.user, 'user_credentials', querystring=querystring)
        expected_data = self.CREDENTIALS_NEXT_API_RESPONSE['results'] + self.CREDENTIALS_API_RESPONSE['results']
        self.assertEqual(actual, expected_data)
