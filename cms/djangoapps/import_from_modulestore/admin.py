"""
This module contains the admin configuration for the Import model.
"""
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from opaque_keys.edx.keys import UsageKey
from opaque_keys import InvalidKeyError

from . import api
from .data import ImportStatus
from .models import Import, PublishableEntityImport, PublishableEntityMapping
from .tasks import save_legacy_content_to_staged_content_task

COMPOSITION_LEVEL_CHOICES = (
    ('xblock', _('XBlock')),
    ('vertical', _('Unit')),
    ('sequential', _('Section')),
    ('chapter', _('Chapter')),
)


def _validate_block_keys(model_admin, request, block_keys_to_import):
    """
    Validate the block keys to import.
    """
    block_keys_to_import = block_keys_to_import.split(',')
    for block_key in block_keys_to_import:
        try:
            UsageKey.from_string(block_key)
        except InvalidKeyError:
            model_admin.message_user(
                request,
                _('Invalid block key: {block_key}').format(block_key=block_key),
                level=messages.ERROR,
            )
            return False
    return True


class ImportActionForm(forms.Form):
    """
    Form for the CourseToLibraryImport action.
    """

    composition_level = forms.ChoiceField(
        choices=COMPOSITION_LEVEL_CHOICES,
        required=False,
        label='Composition Level'
    )
    override = forms.BooleanField(
        required=False,
        label='Override Existing Content'
    )
    block_keys_to_import = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Comma separated list of block keys to import.',
            'rows': 4
        }),
        required=False,
        label='Block Keys to Import'
    )


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
    readonly_fields = ('status',)
    actions = ['import_course_to_library_action']

    def save_model(self, request, obj, form, change):
        """
        Launches the creation of Staged Content after creating a new import instance.
        """
        is_created = not getattr(obj, 'id', None)
        super().save_model(request, obj, form, change)
        if is_created:
            save_legacy_content_to_staged_content_task.apply_async(kwargs={'import_uuid': obj.uuid})

    def import_course_to_library_action(self, request, queryset):
        """
        Import selected courses to the library.
        """
        form = ImportActionForm(request.POST or None)

        if request.POST and 'apply' in request.POST:
            if form.is_valid():
                block_keys_string = form.cleaned_data['block_keys_to_import']
                are_keys_valid = _validate_block_keys(self, request, block_keys_string)
                if not are_keys_valid:
                    return

                target_key_string = block_keys_string.split(',') if block_keys_string else []
                composition_level = form.cleaned_data['composition_level']
                override = form.cleaned_data['override']

                if not queryset.count() == queryset.filter(status=ImportStatus.READY).count():
                    self.message_user(
                        request,
                        _('Only imports with status "Ready" can be imported to the library.'),
                        level=messages.ERROR,
                    )
                    return

                for obj in queryset:
                    api.import_course_staged_content_to_library(
                        usage_ids=target_key_string,
                        import_uuid=str(obj.uuid),
                        user_id=request.user.pk,
                        composition_level=composition_level,
                        override=override,
                    )

                self.message_user(
                    request,
                    _('Importing courses to library.'),
                    level=messages.SUCCESS,
                )

                return HttpResponseRedirect(request.get_full_path())

        return TemplateResponse(
            request,
            'admin/custom_course_import_form.html',
            {
                'form': form,
                'queryset': queryset,
                'action_name': 'import_course_to_library_action',
                'title': _('Import Selected Courses to Library')
            }
        )

    import_course_to_library_action.short_description = _('Import selected courses to library')


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
