"""
django admin pages for program support models
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin

from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramsApiConfigAdmin(ConfigurationModelAdmin):  # pylint: disable=missing-docstring
    pass


admin.site.register(ProgramsApiConfig, ProgramsApiConfigAdmin)
