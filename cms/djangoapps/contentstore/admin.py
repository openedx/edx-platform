"""
Admin site bindings for contentstore
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from contentstore.models import VideoUploadConfig, PushNotificationConfig

admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)
admin.site.register(PushNotificationConfig, ConfigurationModelAdmin)
