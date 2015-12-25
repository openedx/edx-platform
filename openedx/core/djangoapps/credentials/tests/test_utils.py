"""Tests covering Credentials utilities."""
from django.test import TestCase
import httpretty
import mock
from oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin, CredentialsDataMixin
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.utils import (
    get_user_credentials, get_user_program_credentials
)
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.util.mixins import MockApiMixin
from student.tests.factories import UserFactory


class TestCredentialsRetrieval(MockApiMixin, ProgramsApiConfigMixin, CredentialsApiConfigMixin, CredentialsDataMixin,
                               ProgramsDataMixin, TestCase):
    """ Tests covering the retrieval of user credentials from the Credentials
    service.
    """
    def setUp(self):
        super(TestCredentialsRetrieval, self).setUp()

        ClientFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        credential_config = self.create_credential_config()
        self.user = UserFactory()
        self.url = credential_config.internal_api_url + 'user_credentials/?username=' + self.user.username

    @httpretty.activate
    def test_get_user_credentials(self):
        """Verify user credentials data can be retrieve."""
        self.mock_api(self.url, self.CREDENTIALS_API_RESPONSE)

        actual = get_user_credentials(self.user)
        self.assertEqual(actual, self.CREDENTIALS_API_RESPONSE['results'])

    def test_get_user_credentials_credentials_disabled(self):
        """Verify behavior when Credentials is disabled."""
        self.create_credential_config(enabled=False)

        actual = get_user_credentials(self.user)
        self.assertEqual(actual, [])

    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_credentials_client_initialization_failure(self, mock_init):
        """Verify behavior when API client fails to initialize."""
        mock_init.side_effect = Exception

        actual = get_user_credentials(self.user)
        self.assertEqual(actual, [])
        self.assertTrue(mock_init.called)

    @httpretty.activate
    def test_get_user_credentials_retrieval_failure(self):
        """Verify behavior when data can't be retrieved from Credentials."""
        self.mock_api(self.url, self.CREDENTIALS_API_RESPONSE, status_code=500)

        actual = get_user_credentials(self.user)
        self.assertEqual(actual, [])

    def test_get_user_program_credentials_issuance_disable(self):
        """Verify that user program credentials cannot be retrieved if issuance is disabled."""
        self.create_credential_config(enable_learner_issuance=False)
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_user_program_credentials_no_credential(self):
        """Verify behavior if no credential exist."""
        self.mock_api(self.url, {'results': []})
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_user_program_credentials_revoked(self):
        """Verify behavior if credential revoked."""
        credential_data = {"results": [
            {
                "id": 1,
                "username": "test",
                "credential": {
                    "credential_id": 1,
                    "program_id": 1
                },
                "status": "revoked",
                "uuid": "dummy-uuid-1"
            }
        ]}
        self.mock_api(self.url, credential_data)
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_user_program(self):
        """Verify program credentials data can be retrieved and parsed correctly."""
        credentials_config = self.create_credential_config()
        program_config = self.create_program_config()
        program_url = program_config.internal_api_url.strip('/') + '/programs/'
        self.mock_api(program_url, self.PROGRAMS_API_RESPONSE)
        self.mock_api(self.url, self.CREDENTIALS_API_RESPONSE, reset_uri=False)
        actual = get_user_program_credentials(self.user)
        expected = self.PROGRAMS_API_RESPONSE['results']
        expected[0]['credential_url'] = \
            credentials_config.public_service_url + 'credentials/' + self.PROGRAMS_CREDENTIALS_DATA[0]['uuid']
        expected[1]['credential_url'] = \
            credentials_config.public_service_url + 'credentials/' + self.PROGRAMS_CREDENTIALS_DATA[1]['uuid']
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)

        httpretty.reset()
