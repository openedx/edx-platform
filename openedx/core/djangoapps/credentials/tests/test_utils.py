"""Tests covering Credentials utilities."""
import unittest

from django.conf import settings
from django.core.cache import cache
from nose.plugins.attrib import attr
import httpretty
from edx_oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin, CredentialsDataMixin
from openedx.core.djangoapps.credentials.utils import (
    get_user_credentials,
    get_user_program_credentials,
    get_programs_credentials
)
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@attr('shard_2')
class TestCredentialsRetrieval(ProgramsApiConfigMixin, CredentialsApiConfigMixin, CredentialsDataMixin,
                               ProgramsDataMixin, CacheIsolationTestCase):
    """ Tests covering the retrieval of user credentials from the Credentials
    service.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestCredentialsRetrieval, self).setUp()

        ClientFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.user = UserFactory()

        cache.clear()

    def _expected_progam_credentials_data(self):
        """
        Dry method for getting expected program credentials response data.
        """
        return [
            factories.UserCredential(
                id=1,
                username='test',
                credential=factories.ProgramCredential(),
                certificate_url=self.CREDENTIALS_API_RESPONSE['results'][0]['certificate_url'],
            ),
            factories.UserCredential(
                id=2,
                username='test',
                credential=factories.ProgramCredential(),
                certificate_url=self.CREDENTIALS_API_RESPONSE['results'][1]['certificate_url'],
            )
        ]

    def expected_credentials_display_data(self):
        """ Returns expected credentials data to be represented. """
        program_credentials_data = self._expected_progam_credentials_data()
        return [
            {
                'display_name': self.PROGRAMS_API_RESPONSE['results'][0]['name'],
                'subtitle': self.PROGRAMS_API_RESPONSE['results'][0]['subtitle'],
                'credential_url':program_credentials_data[0]['certificate_url']
            },
            {
                'display_name': self.PROGRAMS_API_RESPONSE['results'][1]['name'],
                'subtitle':self.PROGRAMS_API_RESPONSE['results'][1]['subtitle'],
                'credential_url':program_credentials_data[1]['certificate_url']
            }
        ]

    @httpretty.activate
    def test_get_user_credentials(self):
        """Verify user credentials data can be retrieve."""
        self.create_credentials_config()
        self.mock_credentials_api(self.user)

        actual = get_user_credentials(self.user)
        self.assertEqual(actual, self.CREDENTIALS_API_RESPONSE['results'])

    @httpretty.activate
    def test_get_user_credentials_caching(self):
        """Verify that when enabled, the cache is used for non-staff users."""
        self.create_credentials_config(cache_ttl=1)
        self.mock_credentials_api(self.user)

        # Warm up the cache.
        get_user_credentials(self.user)

        # Hit the cache.
        get_user_credentials(self.user)

        # Verify only one request was made.
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

        staff_user = UserFactory(is_staff=True)

        # Hit the Credentials API twice.
        for _ in range(2):
            get_user_credentials(staff_user)

        # Verify that three requests have been made (one for student, two for staff).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 3)

    def test_get_user_program_credentials_issuance_disable(self):
        """Verify that user program credentials cannot be retrieved if issuance is disabled."""
        self.create_credentials_config(enable_learner_issuance=False)
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_user_program_credentials_no_credential(self):
        """Verify behavior if no credential exist."""
        self.create_credentials_config()
        self.mock_credentials_api(self.user, data={'results': []})
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_user_programs_credentials(self):
        """Verify program credentials data can be retrieved and parsed correctly."""
        # create credentials and program configuration
        self.create_credentials_config()
        self.create_programs_config()

        # Mocking the API responses from programs and credentials
        self.mock_programs_api()
        self.mock_credentials_api(self.user, reset_url=False)

        actual = get_user_program_credentials(self.user)
        program_credentials_data = self._expected_progam_credentials_data()
        expected = self.PROGRAMS_API_RESPONSE['results'][:2]
        expected[0]['credential_url'] = program_credentials_data[0]['certificate_url']
        expected[1]['credential_url'] = program_credentials_data[1]['certificate_url']

        # checking response from API is as expected
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)

    @httpretty.activate
    def test_get_user_program_credentials_revoked(self):
        """Verify behavior if credential revoked."""
        self.create_credentials_config()
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
        self.mock_credentials_api(self.user, data=credential_data)
        actual = get_user_program_credentials(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_programs_credentials(self):
        """ Verify that the program credentials data required for display can
        be retrieved.
        """
        # create credentials and program configuration
        self.create_credentials_config()
        self.create_programs_config()

        # Mocking the API responses from programs and credentials
        self.mock_programs_api()
        self.mock_credentials_api(self.user, reset_url=False)
        actual = get_programs_credentials(self.user)
        expected = self.expected_credentials_display_data()

        # Checking result is as expected
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)
