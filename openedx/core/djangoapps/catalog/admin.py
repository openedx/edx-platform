"""
Django admin bindings for catalog support models.
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.catalog.models import CatalogIntegration

admin.site.register(CatalogIntegration, ConfigurationModelAdmin)
