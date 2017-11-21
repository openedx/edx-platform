"""
Django admin for Video Pipeline models.
"""
from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration

admin.site.register(VideoPipelineIntegration, ConfigurationModelAdmin)
