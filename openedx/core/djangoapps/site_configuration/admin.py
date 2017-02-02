"""
Django admin page for Site Configuration models
"""
from django.contrib import admin

from .models import (
    SiteConfiguration,
    SiteConfigurationHistory,
)


class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for the SiteConfiguration object.
    """
    list_display = ('site', 'enabled', 'values')
    search_fields = ('site__domain', 'values')

    class Meta(object):
        """
        Meta class for SiteConfiguration admin model
        """
        model = SiteConfiguration

admin.site.register(SiteConfiguration, SiteConfigurationAdmin)


class SiteConfigurationHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for the SiteConfigurationHistory object.
    """
    list_display = ('site', 'enabled', 'created', 'modified')
    search_fields = ('site__domain', 'values', 'created', 'modified')

    ordering = ['-created']

    class Meta(object):
        """
        Meta class for SiteConfigurationHistory admin model
        """
        model = SiteConfigurationHistory

    def has_add_permission(self, request):
        """Don't allow adds"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletes"""
        return False


admin.site.register(SiteConfigurationHistory, SiteConfigurationHistoryAdmin)
