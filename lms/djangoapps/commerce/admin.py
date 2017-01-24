""" Admin site bindings for commerce app. """

from django.contrib import admin

from commerce.models import CommerceConfiguration
from config_models.admin import ConfigurationModelAdmin

admin.site.register(CommerceConfiguration, ConfigurationModelAdmin)
