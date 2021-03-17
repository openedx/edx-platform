"""
Mixins to test video pipeline integration.
"""

from oauth2_provider.models import Application

from openedx.core.djangoapps.video_pipeline.models import VEMPipelineIntegration


class VideoPipelineMixin(object):
    """
    Utility for working with the VEM video pipeline service during testing.
    """

    vem_pipeline_integration_defaults = {
        'enabled': True,
        'api_url': 'https://video-encode-manager.example.com/api/v1/',
        'service_username': 'cms_vem_pipeline_service_user',
        'client_name': 'vem_pipeline'
    }

    request_uris = 'https://video-pipeline.example.com/api/v1/logout ' \
                   'https://video-pipeline.example.com/api/v1/redirect ' \
                   'https://video-encode-manager.example.com/api/v1/logout ' \
                   'https://video-encode-manager.example.com/api/v1/redirect'

    def create_vem_pipeline_integration(self, **kwargs):
        """
        Creates a new `VEMPipelineIntegration` record with `vem_pipeline_integration_defaults`,
        and it can be updated with any provided overrides
        """
        fields = dict(self.vem_pipeline_integration_defaults, **kwargs)
        return VEMPipelineIntegration.objects.create(**fields)

    def create_video_pipeline_oauth_client(self, user, **kwargs):
        """
        Creates a new `Client` record with `video_pipeline_oauth_client_defaults`,
        and it can be updated with any provided overrides.
        """
        video_pipeline_oauth_client_defaults = {
            'name': 'vem_pipeline',
            'redirect_uris': self.request_uris,
            'client_id': 'vem_client_id',
            'client_secret': 'video_pipeline_client_secret',
            'client_type': Application.CLIENT_CONFIDENTIAL
        }

        fields = dict(video_pipeline_oauth_client_defaults, **kwargs)
        fields['user'] = user
        return Application.objects.create(**fields)
