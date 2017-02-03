"""
Admin site bindings for self-paced courses.
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from .models import SelfPacedConfiguration

admin.site.register(SelfPacedConfiguration, ConfigurationModelAdmin)
