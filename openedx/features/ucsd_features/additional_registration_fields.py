import csv
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django.http import HttpResponse

from openedx.features.ucsd_features.models import AdditionalRegistrationFields


# Form
class AdditionalRegistrationFieldsForm(ModelForm):
    """
    The fields on this form are derived from the AdditionalRegistrationFields model in models.py.
    """
    def __init__(self, *args, **kwargs):
        super(AdditionalRegistrationFieldsForm, self).__init__(*args, **kwargs)

    class Meta(object):
        model = AdditionalRegistrationFields
        fields = ('gender_nb', 'ethnicity', 'age', 'education', 'howheard')


# Admin Customization
class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        field_map = {field.name: field for field in meta.fields}

        header = []
        for field in self.list_display:
            if field in field_map:
                header.append(field_map[field].verbose_name)
            else:
                header.append(field.title())

        writer.writerow(header)
        for obj in queryset:
            row = []
            for field in self.list_display:
                if field in field_map:
                    row.append(getattr(obj, field))
                else:
                    row.append(getattr(self, field)(obj))

            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(AdditionalRegistrationFields)
class AdditionalRegistrationFieldsAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('user_id', 'username', 'email', 'gender_nb', 'ethnicity', 'age', 'education', 'howheard')
    actions = ["export_as_csv"]

    def user_id(self, x):
        return x.user.id

    def username(self, x):
        return x.user.username

    def email(self, x):
        return x.user.email
