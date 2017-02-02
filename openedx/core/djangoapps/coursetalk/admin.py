"""Manage coursetalk configuration. """
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from openedx.core.djangoapps.coursetalk.models import CourseTalkWidgetConfiguration


admin.site.register(CourseTalkWidgetConfiguration, ConfigurationModelAdmin)
