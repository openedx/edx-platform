"""
Admin site bindings for self-paced courses.
"""

from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import SelfPacedConfiguration

admin.site.register(SelfPacedConfiguration, ConfigurationModelAdmin)
