import csv
from logging import getLogger

from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import ExternalId, ExternalIdType

User = get_user_model()

logger = getLogger(__name__)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV File')
    id_type = forms.ModelChoiceField(
        label='External ID Type',
        queryset=ExternalIdType.objects.all()
    )


@admin.register(ExternalId)
class ExternalIdAdmin(admin.ModelAdmin):
    change_list_template = 'admin/external_user_ids/generate_external_user_ids.html'
    list_display = ('user', 'external_user_id', 'external_id_type')
    template = 'openedx/core/djangoapps/external_user_ids/templates/admin/generate_external_ids_template.html'

    def get_urls(self):
        urls = super(ExternalIdAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^bulk_generate_external_ids/$',
                self.admin_site.admin_view(self.generate_ids_form),
                name='bulk_generate_external_ids'
            ),
        ]
        return custom_urls + urls

    def _generate_results_msg(self, user_id_list, unknown_users, created_id_list, existing_id):
        return (
            'Attempted to create for: {}\n'.format(user_id_list) +
            'Could not find: {}\n'.format(unknown_users) +
            'Created External IDs for: {}\n'.format(created_id_list) +
            'External IDs already exist for: {}\n'.format(existing_id)
        )

    def process_generate_ids_request(self, user_id_list, id_type, request, redirect_url):
        created_id_list = []
        existing_id = []

        user_list = User.objects.filter(
            id__in=user_id_list
        )
        for user in user_list:
            new_external_id, created = ExternalId.objects.get_or_create(
                user=user,
                external_id_type=id_type,
            )
            if created:
                created_id_list.append(user.id)
            else:
                existing_id.append(user.id)
        found_user_ids = created_id_list + existing_id
        unknown_users = list(set(user_id_list) - set(found_user_ids))
        result_msg = self._generate_results_msg(user_id_list, unknown_users, created_id_list, existing_id)
        logger.info(result_msg)
        self.message_user(
            request,
            result_msg,
            level=messages.SUCCESS)
        return HttpResponseRedirect(redirect_url)

    def _render_form(self, request, form):
        context = {
            'form': form
        }
        return render(
            request,
            'admin/external_user_ids/generate_external_ids_form.html',
            context
        )

    def generate_ids_form(self, request):
        if request.method == 'POST':
            redirect_url = reverse(
                'admin:external_user_ids_externalid_changelist',
                current_app=self.admin_site.name,
            )
            upload_file = request.FILES.get('csv_file')
            id_type = request.POST.get('id_type')

            if not upload_file or not id_type:
                self.message_user(request, 'CSV file and type are required.', level=messages.ERROR)
                return HttpResponseRedirect(redirect_url)

            try:
                id_type = ExternalIdType.objects.get(id=id_type)
            except ExternalIdType.DoesNotExist:
                self.message_user(request, 'ID Type selected does not exist', level=messages.ERROR)
                return HttpResponseRedirect(redirect_url)

            reader = csv.reader(upload_file.read().decode('utf-8').splitlines())
            headers = next(reader, None)
            if len(headers) != 1 or 'ID' not in headers:
                self.message_user(
                    request,
                    'File is incorrectly formatted. To many columns or incorrectly named ID column',
                    level=messages.ERROR
                )
                return HttpResponseRedirect(redirect_url)
            try:
                user_ids = [int(row[0]) for row in reader]
            except ValueError:
                self.message_user(
                    request,
                    'Data is incorrectly formatted. All ids must be integers',
                    level=messages.ERROR
                )
                return HttpResponseRedirect(redirect_url)

            return self.process_generate_ids_request(user_ids, id_type, request, redirect_url)

        form = CsvImportForm()
        return self._render_form(request, form)
