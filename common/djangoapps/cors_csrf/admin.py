"""Manage cross-domain configuration. """
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from cors_csrf.models import XDomainProxyConfiguration


admin.site.register(XDomainProxyConfiguration, ConfigurationModelAdmin)
