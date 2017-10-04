"""
Model to hold edx-video-pipeline configurations.
"""
from config_models.models import ConfigurationModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _


class VideoPipelineIntegration(ConfigurationModel):
    """
    Manages configuration for connecting to the edx-video-pipeline service and using its API.
    """
    api_url = models.URLField(
        verbose_name=_('Internal API URL'),
        help_text=_('edx-video-pipeline API URL.')
    )

    service_username = models.CharField(
        max_length=100,
        default='video_pipeline_service_user',
        null=False,
        blank=False,
        help_text=_('Username created for Video Pipeline Integration, e.g. video_pipeline_service_user.')
    )

    def get_service_user(self):
        # NOTE: We load the user model here to avoid issues at startup time that result from the hacks
        # in lms/startup.py.
        User = get_user_model()  # pylint: disable=invalid-name
        return User.objects.get(username=self.service_username)
