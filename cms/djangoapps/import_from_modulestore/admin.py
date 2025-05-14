"""
This module contains the admin configuration for the Import model.
"""
from django.contrib import admin
from django.db import transaction

from .forms import ImportCreateForm
from .models import Import, PublishableEntityImport, PublishableEntityMapping
from .tasks import import_to_library_task


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
        'status',
    )
    search_fields = (
        'source_key',
        'target_change',
    )

    raw_id_fields = ('user',)
    readonly_fields = ('status',)

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
            transaction.on_commit(lambda: import_to_library_task.delay(
                obj.pk,
                form.cleaned_data['usage_keys_string'],
                form.cleaned_data['library'].learning_package_id,
                obj.user.pk,
            ))

admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
