"""
Django admin bindings for catalog support models.
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from openedx.core.djangoapps.catalog.models import CatalogIntegration


admin.site.register(CatalogIntegration, ConfigurationModelAdmin)
