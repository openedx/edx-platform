"""Django admin pages for branding configuration. """


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import BrandingApiConfig

admin.site.register(BrandingApiConfig, ConfigurationModelAdmin)
