"""
Django admin dashboard configuration.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from xblock_django.models import XBlockDisableConfig, XBlockConfig, XBlockConfigFlag


class XBlockConfigAdmin(admin.ModelAdmin):
    """Admin for XBlock Configuration"""
    list_display = ('name', 'support_level', 'deprecated')

admin.site.register(XBlockDisableConfig, ConfigurationModelAdmin)
admin.site.register(XBlockConfigFlag, ConfigurationModelAdmin)
admin.site.register(XBlockConfig, XBlockConfigAdmin)
