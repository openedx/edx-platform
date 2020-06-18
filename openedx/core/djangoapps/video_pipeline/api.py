"""
API utils in order to communicate to edx-video-pipeline.
"""

import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from oauth2_provider.models import Application
from slumber.exceptions import HttpClientError

from openedx.core.djangoapps.video_pipeline.config.waffle import ENABLE_VEM_PIPELINE, waffle_flags
from openedx.core.djangoapps.video_pipeline.models import VEMPipelineIntegration, VideoPipelineIntegration
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
    course_key = credentials_payload.pop('course_key', None)

    if course_key and waffle_flags()[ENABLE_VEM_PIPELINE].is_enabled(course_key):
        pipeline_integration = VEMPipelineIntegration.current()
    else:
        pipeline_integration = VideoPipelineIntegration.current()

    if pipeline_integration.enabled:
        try:
            oauth_client = Application.objects.get(name=pipeline_integration.client_name)
        except ObjectDoesNotExist:
            return error_response, is_updated

        client = create_video_pipeline_api_client(
            oauth_client.client_id,
            oauth_client.client_secret
        )
        error_message = "Unable to update transcript credentials -- org={}, provider={}, response={}"
        try:
            response = client.request("POST", pipeline_integration.api_url, json=credentials_payload)
            if response.ok:
                is_updated = True
            else:
                is_updated = False
                error_response = json.loads(response.text)
                log.error(error_message.format(
                    credentials_payload.get('org'),
                    credentials_payload.get('provider'),
                    response.text
                ))
        except HttpClientError as ex:
            is_updated = False
            log.exception(error_message.format(
                credentials_payload.get('org'),
                credentials_payload.get('provider'),
                ex.content
            ))
            error_response = json.loads(ex.content)

    return error_response, is_updated
