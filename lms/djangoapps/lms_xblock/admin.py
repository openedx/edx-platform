"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig

admin.site.register(XBlockAsidesConfig, ConfigurationModelAdmin)
