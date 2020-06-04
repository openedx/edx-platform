"""
Tests for Video Pipeline api utils.
"""

import json

import ddt
from django.test.testcases import TestCase
from mock import Mock, patch
from opaque_keys.edx.locations import CourseLocator
from slumber.exceptions import HttpClientError
from student.tests.factories import UserFactory

from openedx.core.djangoapps.video_pipeline.api import update_3rd_party_transcription_service_credentials
from openedx.core.djangoapps.video_pipeline.config.waffle import ENABLE_VEM_PIPELINE, waffle_flags
from openedx.core.djangoapps.video_pipeline.tests.mixins import VideoPipelineMixin
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag


@ddt.ddt
class TestAPIUtils(VideoPipelineMixin, TestCase):
    """
    Tests for API Utils.
    """
    def setUp(self):
        self.pipeline_integration = self.create_video_pipeline_integration()
        self.user = UserFactory(username=self.pipeline_integration.service_username)
        self.oauth_client = self.create_video_pipeline_oauth_client(user=self.user)

    def add_vem_client(self):
        """
        Creates a VEM oauth client
        """
        self.pipeline_integration = self.create_vem_pipeline_integration()
        self.user = UserFactory(username=self.pipeline_integration.service_username)
        self.oauth_client = self.create_video_pipeline_oauth_client(user=self.user, vem_enabled=True)

    def test_update_transcription_service_credentials_with_integration_disabled(self):
        """
        Test updating the credentials when service integration is disabled.
        """
        self.pipeline_integration.enabled = False
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

    @patch('openedx.core.djangoapps.video_pipeline.api.log')
    @patch('openedx.core.djangoapps.video_pipeline.utils.OAuthAPIClient')
    def test_update_transcription_service_credentials_for_vem(self, mock_client, mock_logger):
        """
        Test that if waffle flag `ENABLE_VEM_PIPELINE` is on for course, then credentials
        are successfully posted to VEM.
        """
        self.add_vem_client()
        course_key = CourseLocator("test_org", "test_course_num", "test_run")
        credentials_payload = {
            'username': 'Jason_cielo_24',
            'api_key': '12345678',
            'course_key': course_key
        }
        mock_client.request.return_value.ok = True

        # Try updating the transcription service credentials
        with override_waffle_flag(waffle_flags()[ENABLE_VEM_PIPELINE], active=True):
            error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)

        # Making sure log.exception is not called.
        self.assertDictEqual(error_response, {})
        self.assertFalse(mock_logger.exception.called)
        self.assertTrue(is_updated)
