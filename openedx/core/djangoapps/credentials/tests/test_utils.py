"""Tests covering Credentials utilities."""
import uuid

from django.core.cache import cache
from edx_oauth2_provider.tests.factories import ClientFactory
import httpretty
import mock
from nose.plugins.attrib import attr
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.catalog.tests import factories as catalog_factories
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin, CredentialsDataMixin
from openedx.core.djangoapps.credentials.utils import (
    get_user_credentials,
    get_user_program_credentials,
    get_programs_credentials,
    get_programs_for_credentials
)
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory


@skip_unless_lms
@attr(shard=2)
class TestCredentialsRetrieval(CredentialsApiConfigMixin, CredentialsDataMixin, CacheIsolationTestCase):
    """ Tests covering the retrieval of user credentials from the Credentials
    service.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestCredentialsRetrieval, self).setUp()

        ClientFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.user = UserFactory()
        self.primary_uuid = str(uuid.uuid4())
        self.alternate_uuid = str(uuid.uuid4())

        cache.clear()

    def expected_credentials_display_data(self, programs):
        """ Returns expected credentials data to be represented. """
        return [
            {
                'display_name': programs[0]['title'],
                'subtitle': programs[0]['subtitle'],
                'credential_url': programs[0]['credential_url']
            },
            {
                'display_name': programs[1]['title'],
                'subtitle': programs[1]['subtitle'],
                'credential_url': programs[1]['credential_url']
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

        # Mocking the API responses from programs and credentials
        primary_uuid, alternate_uuid = str(uuid.uuid4()), str(uuid.uuid4())
        credentials_api_response = {
            "next": None,
            "results": [
                factories.UserCredential(
                    username='test',
                    credential=factories.ProgramCredential(program_uuid=primary_uuid)
                ),
                factories.UserCredential(
                    username='test',
                    credential=factories.ProgramCredential(program_uuid=alternate_uuid)
                )
            ]
        }
        self.mock_credentials_api(self.user, data=credentials_api_response, reset_url=False)
        programs = [
            catalog_factories.Program(uuid=primary_uuid), catalog_factories.Program(uuid=alternate_uuid)
        ]

        with mock.patch("openedx.core.djangoapps.credentials.utils.get_programs_for_credentials") as mock_get_programs:
            mock_get_programs.return_value = programs
            actual = get_user_program_credentials(self.user)

            # checking response from API is as expected
            self.assertEqual(len(actual), 2)
            self.assertEqual(actual, programs)

    @httpretty.activate
    def test_get_programs_credentials(self):
        """ Verify that the program credentials data required for display can
        be retrieved.
        """
        # create credentials and program configuration
        self.create_credentials_config()

        # Mocking the API responses from programs and credentials
        primary_uuid, alternate_uuid = str(uuid.uuid4()), str(uuid.uuid4())
        credentials_api_response = {
            "next": None,
            "results": [
                factories.UserCredential(
                    username='test',
                    credential=factories.ProgramCredential(program_uuid=primary_uuid)
                ),
                factories.UserCredential(
                    username='test',
                    credential=factories.ProgramCredential(program_uuid=alternate_uuid)
                )
            ]
        }
        self.mock_credentials_api(self.user, data=credentials_api_response, reset_url=False)
        programs = [
            catalog_factories.Program(uuid=primary_uuid), catalog_factories.Program(uuid=alternate_uuid)
        ]

        with mock.patch("openedx.core.djangoapps.credentials.utils.get_programs") as mock_get_programs:
            mock_get_programs.return_value = programs
            actual = get_programs_credentials(self.user)
            expected = self.expected_credentials_display_data(programs)

            # Checking result is as expected
            self.assertEqual(len(actual), 2)
            self.assertEqual(actual, expected)

    def _expected_program_credentials_data(self):
        """
        Dry method for getting expected program credentials response data.
        """
        return [
            factories.UserCredential(
                username='test',
                credential=factories.ProgramCredential(
                    program_uuid=self.primary_uuid
                )
            ),
            factories.UserCredential(
                username='test',
                credential=factories.ProgramCredential(
                    program_uuid=self.alternate_uuid
                )
            )
        ]

    def test_get_program_for_certificates(self):
        """Verify programs data can be retrieved and parsed correctly for certificates."""
        programs = [
            catalog_factories.Program(uuid=self.primary_uuid),
            catalog_factories.Program(uuid=self.alternate_uuid)
        ]

        program_credentials_data = self._expected_program_credentials_data()
        with mock.patch("openedx.core.djangoapps.credentials.utils.get_programs") as patched_get_programs:
            patched_get_programs.return_value = programs
            actual = get_programs_for_credentials(self.user, program_credentials_data)

            self.assertEqual(len(actual), 2)
            self.assertEqual(actual, programs)

    def test_get_program_for_certificates_no_data(self):
        """Verify behavior when no programs data is found for the user."""
        program_credentials_data = self._expected_program_credentials_data()
        with mock.patch("openedx.core.djangoapps.credentials.utils.get_programs") as patched_get_programs:
            patched_get_programs.return_value = []
            actual = get_programs_for_credentials(self.user, program_credentials_data)

            self.assertEqual(actual, [])
