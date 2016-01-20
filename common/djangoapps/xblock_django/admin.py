"""
Django admin dashboard configuration.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from xblock_django.models import XBlockDisableConfig, XBlockDeprecatedAdvancedComponentConfig

admin.site.register(XBlockDisableConfig, ConfigurationModelAdmin)
admin.site.register(XBlockDeprecatedAdvancedComponentConfig, ConfigurationModelAdmin)
