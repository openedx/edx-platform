"""Tests covering Credentials utilities."""
import uuid
from unittest import mock

from django.test import override_settings
from edx_toggles.toggles.testutils import override_waffle_switch

from openedx.core.djangoapps.credentials.config import USE_LEARNER_RECORD_MFE
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.credentials.utils import get_credentials, get_credentials_records_url
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory

UTILS_MODULE = 'openedx.core.djangoapps.credentials.utils'


@skip_unless_lms
class TestGetCredentials(CredentialsApiConfigMixin, CacheIsolationTestCase):
    """ Tests for credentials utility functions. """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super().setUp()

        ApplicationFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME)

        self.credentials_config = self.create_credentials_config(cache_ttl=1)
        self.user = UserFactory()

    @mock.patch(UTILS_MODULE + '.get_api_data')
    def test_get_many(self, mock_get_edx_api_data):
        expected = factories.UserCredential.create_batch(3)
        mock_get_edx_api_data.return_value = expected

        actual = get_credentials(self.user)

        mock_get_edx_api_data.assert_called_once()
        call = mock_get_edx_api_data.mock_calls[0]
        __, __, kwargs = call

        querystring = {
            'username': self.user.username,
            'status': 'awarded',
            'only_visible': 'True',
        }
        cache_key = f'{self.credentials_config.CACHE_KEY}.{self.user.username}'
        assert kwargs['querystring'] == querystring
        assert kwargs['cache_key'] == cache_key

        assert actual == expected

    @mock.patch(UTILS_MODULE + '.get_api_data')
    def test_get_one(self, mock_get_edx_api_data):
        expected = factories.UserCredential()
        mock_get_edx_api_data.return_value = expected

        program_uuid = str(uuid.uuid4())
        actual = get_credentials(self.user, program_uuid=program_uuid)

        mock_get_edx_api_data.assert_called_once()
        call = mock_get_edx_api_data.mock_calls[0]
        __, __, kwargs = call

        querystring = {
            'username': self.user.username,
            'status': 'awarded',
            'only_visible': 'True',
            'program_uuid': program_uuid,
        }
        cache_key = f'{self.credentials_config.CACHE_KEY}.{self.user.username}.{program_uuid}'
        assert kwargs['querystring'] == querystring
        assert kwargs['cache_key'] == cache_key

        assert actual == expected

    @mock.patch(UTILS_MODULE + '.get_api_data')
    def test_type_filter(self, mock_get_edx_api_data):
        get_credentials(self.user, credential_type='program')

        mock_get_edx_api_data.assert_called_once()
        call = mock_get_edx_api_data.mock_calls[0]
        __, __, kwargs = call

        querystring = {
            'username': self.user.username,
            'status': 'awarded',
            'only_visible': 'True',
            'type': 'program',
        }
        assert kwargs['querystring'] == querystring

    @override_settings(LEARNER_RECORD_MICROFRONTEND_URL=None)
    @override_settings(CREDENTIALS_PUBLIC_SERVICE_URL="http://foo")
    def test_get_credentials_records_url(self):
        """
        A test that verifies the functionality of the `get_credentials_records_url`. 
        """
        result = get_credentials_records_url()
        assert result == "http://foo/records/"

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result == "http://foo/records/programs/abcdefghijklmnopqrstuvwxyz123456/"

    @override_settings(LEARNER_RECORD_MICROFRONTEND_URL="http://blah")
    @override_settings(CREDENTIALS_PUBLIC_SERVICE_URL="http://foo")
    @override_waffle_switch(USE_LEARNER_RECORD_MFE, False)
    def test_get_credentials_records_mfe_url_waffle_disabled(self):
        """
        A test that verifies the results of the `get_credentials_records_url` function when the
        LEARNER_RECORD_MICROFRONTEND_URL setting exists but the USE_LEARNER_RECORD_MFE waffle flag is disabled.
        """
        result = get_credentials_records_url()
        assert result == "http://foo/records/"

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result == "http://foo/records/programs/abcdefghijklmnopqrstuvwxyz123456/"

    @override_settings(LEARNER_RECORD_MICROFRONTEND_URL="http://blah")
    @override_settings(CREDENTIALS_PUBLIC_SERVICE_URL="http://foo")
    @override_waffle_switch(USE_LEARNER_RECORD_MFE, True)
    def test_get_credentials_records_mfe_url_waffle_enabled(self):
        """
        A test that verifies the results of the `get_credentials_records_url` function when the
        LEARNER_RECORD_MICROFRONTEND_URL setting exists but the USE_LEARNER_RECORD_MFE waffle flag is enabled.
        """
        result = get_credentials_records_url()
        assert result == "http://blah/"

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result == "http://blah/abcdefghijklmnopqrstuvwxyz123456/"

    @override_settings(CREDENTIALS_PUBLIC_SERVICE_URL=None)
    @override_settings(LEARNER_RECORD_MICROFRONTEND_URL=None)
    def test_get_credentials_records_url_expect_none(self):
        """
        A test that verifieis the results of the `get_credentials_records_url` function when the system is configured
        to use neither the Credentials IDA or the Learner Record MFE.
        """
        result = get_credentials_records_url()
        assert result is None

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result is None

    @override_settings(LEARNER_RECORD_MICROFRONTEND_URL="http://blah")
    @override_settings(CREDENTIALS_PUBLIC_SERVICE_URL=None)
    @override_waffle_switch(USE_LEARNER_RECORD_MFE, True)
    def test_get_credentials_records_url_only_mfe_configured(self):
        """
        A test that verifieis the results of the `get_credentials_records_url` function when the system is configured
        to use only the Learner Record MFE.
        """
        result = get_credentials_records_url()
        assert result == "http://blah/"

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result == "http://blah/abcdefghijklmnopqrstuvwxyz123456/"
