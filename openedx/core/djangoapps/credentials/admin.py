"""
Django admin pages for credentials support models.
"""

from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig, NotifyCredentialsConfig


@admin.register(CredentialsApiConfig)
class CredentialsApiConfigAdmin(ConfigurationModelAdmin):
    pass


@admin.register(NotifyCredentialsConfig)
class NotifyCredentialsConfigAdmin(ConfigurationModelAdmin):
    pass
