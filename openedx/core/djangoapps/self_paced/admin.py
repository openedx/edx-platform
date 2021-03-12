"""
Admin site bindings for self-paced courses.
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import SelfPacedConfiguration

admin.site.register(SelfPacedConfiguration, ConfigurationModelAdmin)
