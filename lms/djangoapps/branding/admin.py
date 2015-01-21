'''
django admin pages for branding model
'''
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin

from branding.models import BrandingInfo

admin.site.register(BrandingInfo, ConfigurationModelAdmin)
