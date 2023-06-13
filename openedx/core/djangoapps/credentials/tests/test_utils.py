"""Tests covering Credentials utilities."""
import attr
import uuid
import json
import httpretty
from unittest import mock
from opaque_keys.edx.locator import CourseLocator

from django.test import TestCase
from django.test import override_settings
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests import factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.credentials.utils import (
    get_credentials,
    get_credentials_records_url,
    delete_course_certificate_configuration,
    send_course_certificate_configuration,
)
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.contentstore.signals.handlers import create_course_certificate_config_data

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


@skip_unless_lms
class TestCourseCertificateConfiguration(TestCase):
    """
    Tests for course certificate configurations functions.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username='cred-user')
        self.course_key = CourseLocator(org='TestU', course='sig101', run='Summer2022', branch=None, version_guid=None)
        self.certificate_config_data = attr.asdict(create_course_certificate_config_data(
            str(self.course_key),
            "honor",
            {
                'foo': 'bar',
                'baz': 'foo',
                'is_active': True,
                'signatories': [],
            }
        ))
        self.expected_body_data = {
            'certificate_type': 'honor',
            'course_id': str(self.course_key),
            'title': None,
            'signatories': [],
            'is_active': True,
        }

    @override_settings(CREDENTIALS_SERVICE_USERNAME='cred-user')
    @httpretty.activate
    @mock.patch('openedx.core.djangoapps.credentials.utils.get_credentials_api_base_url')
    def test_course_certificate_config_deleted(self, mock_get_api_base_url):
        """
        Ensure the correct API call when the invoke delete_course_certificate_configuration happened.
        """
        mock_get_api_base_url.return_value = 'http://test-server/'
        httpretty.register_uri(
            httpretty.DELETE,
            'http://test-server/course_certificates/',
            body=json.dumps(self.expected_body_data)
        )
        response = delete_course_certificate_configuration(self.course_key, self.certificate_config_data)
        assert response.status_code == 200
        assert response.json() == self.expected_body_data

    @override_settings(CREDENTIALS_SERVICE_USERNAME='cred-user')
    @httpretty.activate
    @mock.patch('openedx.core.djangoapps.credentials.utils.get_credentials_api_base_url')
    def test_course_certificate_config_sent(self, mock_get_api_base_url):
        """
        Ensure the correct API call when the invoke send_course_certificate_configuration happened.
        """
        mock_get_api_base_url.return_value = 'http://test-server/'
        httpretty.register_uri(
            httpretty.POST,
            'http://test-server/course_certificates/',
            body=json.dumps(self.expected_body_data)
        )
        response = send_course_certificate_configuration(self.course_key, self.certificate_config_data, signature_assets={})
        assert response.status_code == 200
        assert response.json() == self.expected_body_data
