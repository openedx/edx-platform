"""
Admin site bindings for contentstore
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from contentstore.models import VideoUploadConfig

admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)
