"""
Tests for Video Pipeline api utils.
"""

import json

import ddt
from django.test.testcases import TestCase
from mock import Mock, patch
from slumber.exceptions import HttpClientError
from common.djangoapps.student.tests.factories import UserFactory

from openedx.core.djangoapps.video_pipeline.api import update_3rd_party_transcription_service_credentials
from openedx.core.djangoapps.video_pipeline.tests.mixins import VideoPipelineMixin


@ddt.ddt
class TestAPIUtils(VideoPipelineMixin, TestCase):
    """
    Tests for API Utils.
    """
    def setUp(self):
        """
        Setup VEM oauth client.
        """
        self.add_vem_client()

    def add_vem_client(self):
        """
        Creates a VEM oauth client
        """
        self.vem_pipeline_integration = self.create_vem_pipeline_integration()
        self.vem_user = UserFactory(username=self.vem_pipeline_integration.service_username)
        self.vem_oauth_client = self.create_video_pipeline_oauth_client(user=self.vem_user)

    def test_update_transcription_service_credentials_with_vem_disabled(self):
        """
        Test updating the credentials when VEM integration is disabled.
        """
        # Disabling VEM
        self.vem_pipeline_integration.enabled = False
        self.vem_pipeline_integration.save()

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
    @patch('openedx.core.djangoapps.video_pipeline.utils.OAuthAPIClient')
    def test_update_transcription_service_credentials(self, credentials_payload, mock_client, mock_logger):
        """
        Tests that the update transcription service credentials api util works as expected.
        """
        mock_client.request.return_value.ok = True

        # Try updating the transcription service credentials
        error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)

        # Making sure log.exception is not called.
        self.assertDictEqual(error_response, {})
        self.assertFalse(mock_logger.exception.called)
        self.assertTrue(is_updated)

        mock_logger.info.assert_any_call('Sending transcript credentials to VEM for org: {} and provider: {}'.format(
            credentials_payload.get('org'), credentials_payload.get('provider')
        ))

    @patch('openedx.core.djangoapps.video_pipeline.api.log')
    @patch('openedx.core.djangoapps.video_pipeline.utils.OAuthAPIClient')
    def test_update_transcription_service_credentials_exceptions(self, mock_client, mock_logger):
        """
        Tests that the update transcription service credentials logs the exception occurring
        during communication with edx-video-pipeline.
        """
        error_content = '{"error_type": "1"}'
        mock_client.return_value.request = Mock(side_effect=HttpClientError(content=error_content))

        # try updating the transcription service credentials
        credentials_payload = {
            'org': 'mit',
            'provider': 'ABC Provider',
            'api_key': '61c56a8d0'
        }
        error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)

        # Assert the results.
        self.assertFalse(is_updated)
        self.assertDictEqual(error_response, json.loads(error_content))
        mock_logger.exception.assert_called_with(
            'Unable to update transcript credentials -- org={}, provider={}, response={}'.format(
                credentials_payload['org'],
                credentials_payload['provider'],
                error_content
            )
        )
