"""Django admin pages for branding configuration. """
from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import BrandingApiConfig, BrandingInfoConfig

admin.site.register(BrandingInfoConfig, ConfigurationModelAdmin)
admin.site.register(BrandingApiConfig, ConfigurationModelAdmin)
