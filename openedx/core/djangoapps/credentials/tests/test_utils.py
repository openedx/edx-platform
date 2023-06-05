"""Tests covering Credentials utilities."""


import uuid

import mock

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.credentials.utils import get_credentials
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory

UTILS_MODULE = 'openedx.core.djangoapps.credentials.utils'


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.get_edx_api_data')
class TestGetCredentials(CredentialsApiConfigMixin, CacheIsolationTestCase):
    """ Tests for credentials utility functions. """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetCredentials, self).setUp()

        ApplicationFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME)

        self.credentials_config = self.create_credentials_config(cache_ttl=1)
        self.user = UserFactory()

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
        cache_key = '{}.{}'.format(self.credentials_config.CACHE_KEY, self.user.username)
        self.assertEqual(kwargs['querystring'], querystring)
        self.assertEqual(kwargs['cache_key'], cache_key)

        self.assertEqual(actual, expected)

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
        cache_key = '{}.{}.{}'.format(self.credentials_config.CACHE_KEY, self.user.username, program_uuid)
        self.assertEqual(kwargs['querystring'], querystring)
        self.assertEqual(kwargs['cache_key'], cache_key)

        self.assertEqual(actual, expected)

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
        self.assertEqual(kwargs['querystring'], querystring)
