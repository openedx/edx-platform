"""
Admin site bindings for contentstore
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from contentstore.models import VideoEncodingDownloadConfig

admin.site.register(VideoEncodingDownloadConfig, ConfigurationModelAdmin)
