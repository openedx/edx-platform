"""
Django admin pages for credentials support models.
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


class CredentialsApiConfigAdmin(ConfigurationModelAdmin):  # pylint: disable=missing-docstring
    pass


admin.site.register(CredentialsApiConfig, CredentialsApiConfigAdmin)
