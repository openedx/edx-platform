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
        'created',
        'status',
        'source_key',
        'target_change',
    )
    list_filter = (
        'user_task_status__state',
    )
    search_fields = (
        'source_key',
        'target_change',
    )

    raw_id_fields = ('user',)
    readonly_fields = ('user_task_status',)

    def uuid(self, obj):
        """
        Returns the UUID of the import.
        """
        return getattr(obj.user_task_status, 'uuid', None)

    def created(self, obj):
        """
        Returns the creation date of the import.
        """
        return getattr(obj.user_task_status, 'created', None)

    def status(self, obj):
        """
        Returns the status of the import.
        """
        return getattr(obj.user_task_status, 'state', None)


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
