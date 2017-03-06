"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from mobile_api.models import MobileApiConfig, AppVersionConfig

admin.site.register(MobileApiConfig, ConfigurationModelAdmin)


class AppVersionConfigAdmin(admin.ModelAdmin):
    """ Admin class for AppVersionConfig model """
    fields = ('platform', 'version', 'expire_at', 'enabled')
    list_filter = ['platform']

    class Meta(object):
        ordering = ['-major_version', '-minor_version', '-patch_version']

    def get_list_display(self, __):
        """ defines fields to display in list view """
        return ['platform', 'version', 'expire_at', 'enabled', 'created_at', 'updated_at']

admin.site.register(AppVersionConfig, AppVersionConfigAdmin)
