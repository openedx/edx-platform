"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from mobile_api.models import MobileApiConfig

admin.site.register(MobileApiConfig, ConfigurationModelAdmin)
