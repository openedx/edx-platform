"""
Django admin XBlock support configuration.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from xblock_django.models import XBlockDisableConfig, XBlockConfig, XBlockConfigFlag
from simple_history.admin import SimpleHistoryAdmin


class XBlockConfigAdmin(SimpleHistoryAdmin):
    """Admin for XBlock Configuration"""
    list_display = ('name', 'template', 'support_level', 'deprecated', 'changed_by', 'change_date')

admin.site.register(XBlockDisableConfig, ConfigurationModelAdmin)
admin.site.register(XBlockConfigFlag, ConfigurationModelAdmin)
admin.site.register(XBlockConfig, XBlockConfigAdmin)
