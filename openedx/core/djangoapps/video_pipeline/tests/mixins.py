"""
Mixins to test video pipeline integration.
"""
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import Client

from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration


class VideoPipelineIntegrationMixin(object):
    """
    Utility for working with the video pipeline service during testing.
    """
    video_pipeline_integration_defaults = {
        'enabled': True,
        'api_url': 'https://video-pipeline.example.com/api/v1/',
        'service_username': 'cms_video_pipeline_service_user',
        'client_name': 'video_pipeline'
    }

    video_pipelien_oauth_client_defaults = {
        'name': 'video_pipeline',
        'url': 'https://video-pipeline.example.com/api/v1/',
        'redirect_uri': 'https://video-pipeline.example.com/api/v1/redirect',
        'logout_uri': 'https://video-pipeline.example.com/api/v1/logout',
        'client_id': 'video_pipeline_client_id',
        'client_secret': 'video_pipeline_client_secret',
        'client_type': CONFIDENTIAL
    }

    def create_video_pipeline_integration(self, **kwargs):
        """
        Creates a new `VideoPipelineIntegration` record with `video_pipeline_integration_defaults`,
        and it can be updated with any provided overrides.
        """
        fields = dict(self.video_pipeline_integration_defaults, **kwargs)
        return VideoPipelineIntegration.objects.create(**fields)

    def create_video_pipeline_oauth_client(self, user, **kwargs):
        """
        Creates a new `Client` record with `video_pipelien_oauth_client_defaults`,
        and it can be updated with any provided overrides.
        """
        fields = dict(self.video_pipelien_oauth_client_defaults, **kwargs)
        fields['user'] = user
        return Client.objects.create(**fields)
