"""Tests covering Credentials utilities."""
import uuid
from unittest import mock

from django.conf import settings
from requests import Response
from requests.exceptions import HTTPError

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.credentials.utils import (
    get_courses_completion_status,
    get_credentials,
    get_credentials_records_url
)
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms

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

    def test_get_credentials_records_url(self):
        """
        A test that verifies the functionality of the `get_credentials_records_url`.
        """
        result = get_credentials_records_url()
        assert result == "https://credentials.example.com/records/"

        result = get_credentials_records_url("abcdefgh-ijkl-mnop-qrst-uvwxyz123456")
        assert result == "https://credentials.example.com/records/programs/abcdefghijklmnopqrstuvwxyz123456"

    @mock.patch('requests.Response.raise_for_status')
    @mock.patch('requests.Response.json')
    @mock.patch(UTILS_MODULE + '.get_credentials_api_client')
    def test_get_courses_completion_status(self, mock_get_api_client, mock_json, mock_raise):
        """
        Test to verify the functionality of get_courses_completion_status
        """
        UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)
        course_statuses = factories.UserCredentialsCourseRunStatus.create_batch(3)
        response_data = [course_status['course_run']['key'] for course_status in course_statuses]
        mock_raise.return_value = None
        mock_json.return_value = {'lms_user_id': self.user.id,
                                  'status': course_statuses,
                                  'username': self.user.username}
        mock_get_api_client.return_value.post.return_value = Response()
        course_run_keys = [course_status['course_run']['key'] for course_status in course_statuses]
        api_response, is_exception = get_courses_completion_status(self.user.id, course_run_keys)
        assert api_response == response_data
        assert is_exception is False

    @mock.patch('requests.Response.raise_for_status')
    def test_get_courses_completion_status_api_error(self, mock_raise):
        mock_raise.return_value = HTTPError('An Error occured')
        UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)
        api_response, is_exception = get_courses_completion_status(self.user.id, ['fake1', 'fake2', 'fake3'])
        assert api_response == []
        assert is_exception is True
