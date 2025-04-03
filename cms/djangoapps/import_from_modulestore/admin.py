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
        'uuid',
        'status',
        'source_key',
        'target',
    )
    list_filter = (
        'status',
    )
    search_fields = (
        'source_key',
        'target',
    )

    raw_id_fields = ('user',)


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
