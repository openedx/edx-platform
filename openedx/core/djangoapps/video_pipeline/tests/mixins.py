"""
Mixins to test video pipeline integration.
"""
from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration


class VideoPipelineIntegrationMixin(object):
    """
    Utility for working with the video pipeline service during testing.
    """
    video_pipeline_integration_defaults = {
        'enabled': True,
        'api_url': 'https://video-pipeline.example.com/api/v1/',
        'service_username': 'cms_video_pipeline_service_user',
    }

    def create_video_pipeline_integration(self, **kwargs):
        """
        Creates a new `VideoPipelineIntegration` record with `video_pipeline_integration_defaults`,
        and it can be updated with any provided overrides.
        """
        fields = dict(self.video_pipeline_integration_defaults, **kwargs)
        return VideoPipelineIntegration.objects.create(**fields)
