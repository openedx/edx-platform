"""
Mixins to test video pipeline integration.
"""

from oauth2_provider.models import Application

from openedx.core.djangoapps.video_pipeline.models import VEMPipelineIntegration, VideoPipelineIntegration


class VideoPipelineMixin(object):
    """
    Utility for working with the video pipelines (VEDA and VEM) service during testing.
    """
    veda_pipeline_integration_defaults = {
        'enabled': True,
        'api_url': 'https://video-pipeline.example.com/api/v1/',
        'service_username': 'cms_veda_pipeline_service_user',
        'client_name': 'veda_pipeline'
    }

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

    def create_video_pipeline_integration(self, **kwargs):
        """
        Creates a new `VideoPipelineIntegration` record with `veda_pipeline_integration_defaults`,
        and it can be updated with any provided overrides.
        """
        fields = dict(self.veda_pipeline_integration_defaults, **kwargs)
        return VideoPipelineIntegration.objects.create(**fields)

    def create_vem_pipeline_integration(self, **kwargs):
        """
        Creates a new `VEMPipelineIntegration` record with `vem_pipeline_integration_defaults`,
        and it can be updated with any provided overrides
        """
        fields = dict(self.vem_pipeline_integration_defaults, **kwargs)
        return VEMPipelineIntegration.objects.create(**fields)

    def create_video_pipeline_oauth_client(self, user, vem_enabled=False, **kwargs):
        """
        Creates a new `Client` record with `video_pipeline_oauth_client_defaults`,
        and it can be updated with any provided overrides.
        """
        video_pipeline_oauth_client_defaults = {
            'name': 'vem_pipeline' if vem_enabled else 'veda_pipeline',
            'redirect_uris': self.request_uris,
            'client_id': 'vem_client_id' if vem_enabled else 'video_pipeline_client_id',
            'client_secret': 'video_pipeline_client_secret',
            'client_type': Application.CLIENT_CONFIDENTIAL
        }

        fields = dict(video_pipeline_oauth_client_defaults, **kwargs)
        fields['user'] = user
        return Application.objects.create(**fields)
