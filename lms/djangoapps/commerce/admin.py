""" Admin site bindings for commerce app. """

from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import CommerceConfiguration

admin.site.register(CommerceConfiguration, ConfigurationModelAdmin)
