"""
This module contains the admin configuration for the Import model.
"""
from django.contrib import admin

from .api import import_to_library
from .forms import ImportCreateForm
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
    uuid.short_description = 'UUID'

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

    def get_form(self, request, obj=None, change=None, **kwargs):
        if not obj:
            return ImportCreateForm
        return super().get_form(request, obj, change, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        Launches the creation of Staged Content after creating a new import instance.
        """
        is_created = not getattr(obj, 'id', None)
        super().save_model(request, obj, form, change)

        if is_created:
            _import, _ = import_to_library(
                source_key=form.cleaned_data['source_key'],
                usage_ids=form.cleaned_data['usage_keys_string'],
                target_learning_package_id=form.cleaned_data['library'].pk,
                user_id=form.cleaned_data['user'].pk,
                composition_level=form.cleaned_data['composition_level'],
                override=form.cleaned_data['override'],
            )
            _import.target_change = form.cleaned_data['target_change']
            _import.save(update_fields=['target_change'])


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
