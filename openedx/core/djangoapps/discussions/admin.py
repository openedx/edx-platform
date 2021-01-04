"""
Customize the django admin experience
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import DiscussionsConfiguration


class DiscussionsConfigurationAdmin(SimpleHistoryAdmin):
    search_fields = (
        'context_key',
        'enabled',
        'provider_type',
    )
    list_filter = (
        'enabled',
        'provider_type',
    )


admin.site.register(DiscussionsConfiguration, DiscussionsConfigurationAdmin)
