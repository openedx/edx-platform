"""Admin views for API managment."""
from django.contrib import admin

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest


@admin.register(ApiAccessRequest)
class ApiAccessRequestAdmin(admin.ModelAdmin):
    """Admin for API access requests."""
    list_display = ('user', 'status', 'website')
    list_filter = ('status',)
    search_fields = ('user__email',)
