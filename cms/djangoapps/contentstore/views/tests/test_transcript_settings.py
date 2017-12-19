import json

import ddt
from django.test.testcases import TestCase
from mock import Mock, patch

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from contentstore.views.transcript_settings import TranscriptionProviderErrorType, validate_transcript_credentials


@ddt.ddt
@patch(
    'openedx.core.djangoapps.video_config.models.VideoTranscriptEnabledFlag.feature_enabled',
    Mock(return_value=True)
)
class TranscriptCredentialsTest(CourseTestCase):
    """
    Tests for transcript credentials handler.
    """
    VIEW_NAME = 'transcript_credentials_handler'

    def get_url_for_course_key(self, course_id):
        return reverse_course_url(self.VIEW_NAME, course_id)

    def test_302_with_anonymous_user(self):
        """
        Verify that redirection happens in case of unauthorized request.
        """
        self.client.logout()
        transcript_credentials_url = self.get_url_for_course_key(self.course.id)
        response = self.client.post(transcript_credentials_url, content_type='application/json')
        self.assertEqual(response.status_code, 302)

    def test_405_with_not_allowed_request_method(self):
        """
        Verify that 405 is returned in case of not-allowed request methods.
        Allowed request methods include POST.
        """
        transcript_credentials_url = self.get_url_for_course_key(self.course.id)
        response = self.client.get(transcript_credentials_url, content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def test_404_with_feature_disabled(self):
        """
        Verify that 404 is returned if the corresponding feature is disabled.
        """
        transcript_credentials_url = self.get_url_for_course_key(self.course.id)
        with patch('openedx.core.djangoapps.video_config.models.VideoTranscriptEnabledFlag.feature_enabled') as feature:
            feature.return_value = False
            response = self.client.post(transcript_credentials_url, content_type='application/json')
            self.assertEqual(response.status_code, 404)

    @ddt.data(
        (
            {
                'provider': 'abc_provider',
                'api_key': '1234'
            },
            ({}, None),
            400,
            '{\n  "error": "Invalid Provider abc_provider."\n}'
        ),
        (
            {
                'provider': '3PlayMedia',
                'api_key': '11111',
                'api_secret_key': '44444'
            },
            ({'error_type': TranscriptionProviderErrorType.INVALID_CREDENTIALS}, False),
            400,
            '{\n  "error": "The information you entered is incorrect."\n}'
        ),
        (
            {
                'provider': 'Cielo24',
                'api_key': '12345',
                'username': 'test_user'
            },
            ({}, True),
            200,
            ''
        )
    )
    @ddt.unpack
    @patch('contentstore.views.transcript_settings.update_3rd_party_transcription_service_credentials')
    def test_transcript_credentials_handler(self, request_payload, update_credentials_response, expected_status_code,
                                            expected_response, mock_update_credentials):
        """
        Tests that transcript credentials handler works as expected.
        """
        mock_update_credentials.return_value = update_credentials_response
        transcript_credentials_url = self.get_url_for_course_key(self.course.id)
        response = self.client.post(
            transcript_credentials_url,
            data=json.dumps(request_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response.content, expected_response)


@ddt.ddt
class TranscriptCredentialsValidationTest(TestCase):
    """
    Tests for credentials validations.
    """

    @ddt.data(
        (
            'ABC',
            {
                'username': 'test_user',
                'password': 'test_pass'
            },
            'Invalid Provider ABC.',
            {}
        ),
        (
            'Cielo24',
            {
                'username': 'test_user'
            },
            'api_key must be specified.',
            {}
        ),
        (
            'Cielo24',
            {
                'username': 'test_user',
                'api_key': 'test_api_key',
                'extra_param': 'extra_value'
            },
            '',
            {
                'username': 'test_user',
                'api_key': 'test_api_key'
            }
        ),
        (
            '3PlayMedia',
            {
                'username': 'test_user'
            },
            'api_key and api_secret_key must be specified.',
            {}
        ),
        (
            '3PlayMedia',
            {
                'api_key': 'test_key',
                'api_secret_key': 'test_secret',
                'extra_param': 'extra_value'
            },
            '',
            {
                'api_key': 'test_key',
                'api_secret_key': 'test_secret'
            }
        ),

    )
    @ddt.unpack
    def test_invalid_credentials(self, provider, credentials, expected_error_message, expected_validated_credentials):
        """
        Test validation with invalid transcript credentials.
        """
        error_message, validated_credentials = validate_transcript_credentials(provider, **credentials)
        # Assert the results.
        self.assertEqual(error_message, expected_error_message)
        self.assertDictEqual(validated_credentials, expected_validated_credentials)
