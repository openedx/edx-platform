"""
Admin site bindings for contentstore
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from cms.djangoapps.contentstore.models import VideoUploadConfig

admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)
