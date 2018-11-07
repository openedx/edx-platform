"""
API utils in order to communicate to edx-video-pipeline.
"""
import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from provider.oauth2.models import Client
from slumber.exceptions import HttpClientError

from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration
from openedx.core.djangoapps.video_pipeline.utils import create_video_pipeline_api_client


log = logging.getLogger(__name__)


def update_3rd_party_transcription_service_credentials(**credentials_payload):
    """
    Updates the 3rd party transcription service's credentials.

    Arguments:
        credentials_payload(dict): A payload containing org, provider and its credentials.

    Returns:
        A Boolean specifying whether the credentials were updated or not
        and an error response received from pipeline.
    """
    error_response, is_updated = {}, False
    pipeline_integration = VideoPipelineIntegration.current()
    if pipeline_integration.enabled:
        try:
            video_pipeline_user = pipeline_integration.get_service_user()
            oauth_client = Client.objects.get(name=pipeline_integration.client_name)
        except ObjectDoesNotExist:
            return error_response, is_updated

        client = create_video_pipeline_api_client(
            user=video_pipeline_user,
            api_client_id=oauth_client.client_id,
            api_client_secret=oauth_client.client_secret,
            api_url=pipeline_integration.api_url
        )

        try:
            client.transcript_credentials.post(credentials_payload)
            is_updated = True
        except HttpClientError as ex:
            is_updated = False
            log.exception(
                ('[video-pipeline-service] Unable to update transcript credentials '
                 '-- org=%s -- provider=%s -- response=%s.'),
                credentials_payload.get('org'),
                credentials_payload.get('provider'),
                ex.content,
            )
            error_response = json.loads(ex.content)

    return error_response, is_updated
