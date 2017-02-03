"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from xblock_config.models import StudioConfig

admin.site.register(StudioConfig, ConfigurationModelAdmin)
