"""
This module contains the admin configuration for the Import model.
"""
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from opaque_keys.edx.keys import UsageKey
from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.content_libraries.api import ContentLibrary, ContainerType

from .api import import_staged_content_to_library
from .data import CompositionLevel, ImportStatus
from .models import Import, PublishableEntityImport, PublishableEntityMapping
from .tasks import save_legacy_content_to_staged_content_task


COMPOSITION_LEVEL_CHOICES = (
    (CompositionLevel.COMPONENT.value, CompositionLevel.COMPONENT.value),
    (ContainerType.Unit.olx_tag, ContainerType.Unit.value),
    (ContainerType.Subsection.olx_tag, ContainerType.Subsection.value),
    (ContainerType.Section.olx_tag, ContainerType.Section.value),
)


class ImportActionForm(forms.Form):
    """
    Form for the CourseToLibraryImport action.
    """

    library = forms.ModelChoiceField(queryset=ContentLibrary.objects.all(), required=False)
    block_keys_to_import = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Comma separated list of block keys to import.',
        }),
        required=False,
        label=_('Block Keys to Import'),
    )
    composition_level = forms.ChoiceField(
        choices=COMPOSITION_LEVEL_CHOICES,
        required=False,
        label=_('Composition Level')
    )
    override = forms.BooleanField(required=False, label=_('Override Existing Content'))

    def clean(self):
        cleaned_data = super().clean()
        required_together = ['block_keys_to_import', 'composition_level', 'library']
        values = [cleaned_data.get(field) for field in required_together]

        if not (all(values) or not any(values)):
            raise forms.ValidationError(
                _('Fields %(fields)s must be filled.'),
                code='invalid',
                params={'fields': ', '.join(required_together)},
            )

        try:
            [
                UsageKey.from_string(key.strip())
                for key in cleaned_data['block_keys_to_import'].split(',') if key.strip()
            ]
        except InvalidKeyError:
            raise forms.ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                _('Invalid block keys format.'),
                code='invalid',
            )

        return cleaned_data


class ImportAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Import model.
    """

    list_display = (
        'uuid',
        'created',
        'status',
        'source_key',
        'run_save_legacy_content'
    )
    list_filter = (
        'status',
    )
    search_fields = (
        'source_key',
    )

    raw_id_fields = ('user',)
    readonly_fields = ('status', 'target_change')
    actions = ['import_content_to_library_action']

    @admin.display(description='Save Legacy Content')
    def run_save_legacy_content(self, obj):
        """
        Render a button to trigger save_legacy_content_to_staged_content for the specific record.
        """
        if obj.status != ImportStatus.NOT_STARTED:
            return

        return format_html(
            f'<a href="{reverse("admin:run-save-legacy-content", args=[obj.pk])}">Stage Content for Import</a>'
        )

    def get_urls(self):
        """
        Add a custom URL for handling the button action.
        """
        return [
            path(
                '<int:pk>/run-save-legacy-content/',
                self.admin_site.admin_view(self.save_legacy_content_to_staged_content),
                name='run-save-legacy-content',
            ),
        ] + super().get_urls()

    def save_legacy_content_to_staged_content(self, request, pk):
        """
        Save legacy content to staged content.

        This action is only available for imports with status "Waiting to stage content".
        Since creating staged content can be a rather resource-intensive operation (for example,
        in the case of several large courses), it is better to run it for individual records.
        """
        redirect_url = reverse('admin:import_from_modulestore_import_changelist')
        try:
            obj = Import.objects.get(pk=pk)
        except Import.DoesNotExist:
            self.message_user(
                request,
                _('Import not found.'),
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_url)
        if obj.status != ImportStatus.NOT_STARTED:
            self.message_user(
                request,
                _('Only imports with status "Waiting to stage content" can be staged.'),
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_url)
        if obj.user != request.user:
            self.message_user(
                request,
                _('You can only stage your own imports.'),
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_url)

        save_legacy_content_to_staged_content_task.delay_on_commit(obj.uuid)
        self.message_user(
            request,
            _('Staged content creation started.'),
            level=messages.SUCCESS,
        )

        return HttpResponseRedirect(redirect_url)

    @admin.action(description=_('Import selected content to library'))
    def import_content_to_library_action(self, request, queryset):
        """
        Import selected content to the library from the related staged content.
        """
        form = ImportActionForm(request.POST or None)

        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.opts,
            'form': form,
            'queryset': queryset,
            'action_name': 'import_content_to_library_action',
            'title': _('Import Selected Content to Library'),
            'original': _('Import Content to Library'),
        })

        if not form.is_valid():
            return TemplateResponse(request, 'admin/custom_content_import_form.html', context)

        if request.POST and 'apply' in request.POST:
            if queryset.count() != queryset.filter(status=ImportStatus.STAGED).count():
                self.message_user(
                    request,
                    _('Only imports with status "Ready" can be imported to the library.'),
                    level=messages.ERROR,
                )
                return

            for obj in queryset:
                import_staged_content_to_library(
                    form.cleaned_data['block_keys_to_import'].split(','),
                    str(obj.uuid),
                    form.cleaned_data['library'].learning_package_id,
                    request.user.pk,
                    composition_level=form.cleaned_data['composition_level'],
                    override=form.cleaned_data['override'],
                )

            self.message_user(
                request,
                _('Importing content to library started.'),
                level=messages.SUCCESS,
            )

            return HttpResponseRedirect(request.get_full_path())

        return TemplateResponse(request, 'admin/custom_content_import_form.html', context)


admin.site.register(Import, ImportAdmin)
admin.site.register(PublishableEntityImport)
admin.site.register(PublishableEntityMapping)
