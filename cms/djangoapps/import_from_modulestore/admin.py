"""
This module contains the admin configuration for the Import model.
"""
from django.contrib import admin

from .models import Import, PublishableEntityImport, PublishableEntityMapping


class ImportAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Import model.
    """

    list_display = (
        'created',
        'source_key',
        'target_key',
        'override',
        'composition_level',
        'target_change',
    )
    search_fields = (
        'source_key',
        'target_key',
        'target_change',
    )


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
