"""
Admin site bindings for dark_lang
"""

from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.dark_lang.models import DarkLangConfig

admin.site.register(DarkLangConfig, ConfigurationModelAdmin)
