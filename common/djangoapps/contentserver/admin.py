"""
Django admin page for CourseAssetCacheTtlConfig, which allows you to configure the TTL
that gets used when sending cachability headers back with request course assets.
"""
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from .models import CourseAssetCacheTtlConfig


class CourseAssetCacheTtlConfigAdmin(ConfigurationModelAdmin):
    """
    Basic configuration for cache TTL.
    """
    list_display = [
        'cache_ttl'
    ]

    def get_list_display(self, request):
        """
        Restore default list_display behavior.

        ConfigurationModelAdmin overrides this, but in a way that doesn't
        respect the ordering. This lets us customize it the usual Django admin
        way.
        """
        return self.list_display


admin.site.register(CourseAssetCacheTtlConfig, CourseAssetCacheTtlConfigAdmin)
