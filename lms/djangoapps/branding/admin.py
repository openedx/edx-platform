"""Django admin pages for branding configuration. """
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin

from .models import BrandingInfoConfig, BrandingApiConfig

admin.site.register(BrandingInfoConfig, ConfigurationModelAdmin)
admin.site.register(BrandingApiConfig, ConfigurationModelAdmin)
