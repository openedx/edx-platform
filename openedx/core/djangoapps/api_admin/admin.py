"""Admin views for API managment."""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig


@admin.register(ApiAccessRequest)
class ApiAccessRequestAdmin(admin.ModelAdmin):
    """Admin for API access requests."""
    list_display = ('user', 'status', 'website')
    list_filter = ('status',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)


admin.site.register(ApiAccessConfig, ConfigurationModelAdmin)
