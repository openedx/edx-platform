"""
Tests for Video Pipeline api utils.
"""

import ddt
import json
from mock import Mock, patch

from django.test.testcases import TestCase
from slumber.exceptions import HttpClientError

from student.tests.factories import UserFactory

from openedx.core.djangoapps.video_pipeline.api import update_3rd_party_transcription_service_credentials
from openedx.core.djangoapps.video_pipeline.tests.mixins import VideoPipelineIntegrationMixin


@ddt.ddt
class TestAPIUtils(VideoPipelineIntegrationMixin, TestCase):
    """
    Tests for API Utils.
    """
    def setUp(self):
        self.pipeline_integration = self.create_video_pipeline_integration()
        self.user = UserFactory(username=self.pipeline_integration.service_username)
        self.oauth_client = self.create_video_pipeline_oauth_client(user=self.user)

    def test_update_transcription_service_credentials_with_integration_disabled(self):
        """
        Test updating the credentials when service integration is disabled.
        """
        self.pipeline_integration.enabled = False
        self.pipeline_integration.save()
        __, is_updated = update_3rd_party_transcription_service_credentials()
        self.assertFalse(is_updated)

    def test_update_transcription_service_credentials_with_unknown_user(self):
        """
        Test updating the credentials when expected service user is not registered.
        """
        self.pipeline_integration.service_username = 'non_existent_user'
        self.pipeline_integration.save()
        __, is_updated = update_3rd_party_transcription_service_credentials()
        self.assertFalse(is_updated)

    def test_update_transcription_service_credentials_with_unknown_oauth_client(self):
        """
        Test updating the credentials when expected oauth cleint is not present.
        """
        self.pipeline_integration.client_name = 'non_existent_client'
        self.pipeline_integration.save()
        __, is_updated = update_3rd_party_transcription_service_credentials()
        self.assertFalse(is_updated)

    @ddt.data(
        {
            'username': 'Jason_cielo_24',
            'api_key': '12345678',
        },
        {
            'api_key': '12345678',
            'api_secret': '11111111',
        }
    )
    @patch('openedx.core.djangoapps.video_pipeline.api.log')
    @patch('openedx.core.djangoapps.video_pipeline.utils.EdxRestApiClient')
    def test_update_transcription_service_credentials(self, credentials_payload, mock_client, mock_logger):
        """
        Tests that the update transcription service credentials api util works as expected.
        """
        # Mock the post request
        mock_credentials_endpoint = mock_client.return_value.transcript_credentials
        # Try updating the transcription service credentials
        error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)

        mock_credentials_endpoint.post.assert_called_with(credentials_payload)
        # Making sure log.exception is not called.
        self.assertDictEqual(error_response, {})
        self.assertFalse(mock_logger.exception.called)
        self.assertTrue(is_updated)

    @patch('openedx.core.djangoapps.video_pipeline.api.log')
    @patch('openedx.core.djangoapps.video_pipeline.utils.EdxRestApiClient')
    def test_update_transcription_service_credentials_exceptions(self, mock_client, mock_logger):
        """
        Tests that the update transcription service credentials logs the exception occurring
        during communication with edx-video-pipeline.
        """
        error_content = '{"error_type": "1"}'
        # Mock the post request
        mock_credentials_endpoint = mock_client.return_value.transcript_credentials
        mock_credentials_endpoint.post = Mock(side_effect=HttpClientError(content=error_content))
        # try updating the transcription service credentials
        credentials_payload = {
            'org': 'mit',
            'provider': 'ABC Provider',
            'api_key': '61c56a8d0'
        }
        error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)

        mock_credentials_endpoint.post.assert_called_with(credentials_payload)
        # Assert the results.
        self.assertFalse(is_updated)
        self.assertDictEqual(error_response, json.loads(error_content))
        mock_logger.exception.assert_called_with(
            u'[video-pipeline-service] Unable to update transcript credentials -- org=%s -- provider=%s -- response=%s.',
            credentials_payload['org'],
            credentials_payload['provider'],
            error_content
        )
