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

    class Meta(object):
        model = AdditionalRegistrationFields
        fields = ('gender_nb', 'ethnicity', 'age', 'education', 'howheard')
        error_messages = {
            'gender_nb': {
                'required': 'Please select your Gender.',
            },
            'ethnicity': {
                'required': 'Please select your Ethnicity.',
            },
            'age': {
                'required': 'Please select your Age Group.',
            },
            'education': {
                'required': 'Please select your Education Level.',
            },
            'howheard': {
                'required': 'Please tell, how did you hear about us.'
            },
        }
        help_texts = {
            'gender_nb': 'Select "Decline to State" if you prefer not to tell.',
            'ethnicity': 'The ethnic or social group you belong to.',
            'age': 'Select the range in which your current age falls.',
            'education': 'Your most recent educational qualification.',
            'howheard': 'From where did you learn about us?',
        }


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
