'''
Django admin pages for Video Branding Configuration.
'''
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin

from .models import BrandingInfoConfig

admin.site.register(BrandingInfoConfig, ConfigurationModelAdmin)
