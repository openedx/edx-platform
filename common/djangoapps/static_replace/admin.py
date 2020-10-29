"""
Django admin page for AssetBaseUrlConfig, which allows you to set the base URL
that gets prepended to asset URLs in order to serve them from, say, a CDN.
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import AssetBaseUrlConfig, AssetExcludedExtensionsConfig


class AssetBaseUrlConfigAdmin(ConfigurationModelAdmin):
    """
    Basic configuration for asset base URL.
    """
    list_display = [
        'base_url'
    ]

    def get_list_display(self, request):
        """
        Restore default list_display behavior.

        ConfigurationModelAdmin overrides this, but in a way that doesn't
        respect the ordering. This lets us customize it the usual Django admin
        way.
        """
        return self.list_display


class AssetExcludedExtensionsConfigAdmin(ConfigurationModelAdmin):
    """
    Basic configuration for asset base URL.
    """
    list_display = [
        'excluded_extensions'
    ]

    def get_list_display(self, request):
        """
        Restore default list_display behavior.

        ConfigurationModelAdmin overrides this, but in a way that doesn't
        respect the ordering. This lets us customize it the usual Django admin
        way.
        """
        return self.list_display


admin.site.register(AssetBaseUrlConfig, AssetBaseUrlConfigAdmin)
admin.site.register(AssetExcludedExtensionsConfig, AssetExcludedExtensionsConfigAdmin)
