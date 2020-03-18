import csv
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django.http import HttpResponse

# Backwards compatible settings.AUTH_USER_MODEL
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# Models
class AdditionalRegistrationFields(models.Model):
    """
    This model contains two extra fields that will be saved when a user registers.
    The form that wraps this model is in the forms.py file.
    """
    user = models.OneToOneField(USER_MODEL, null=True)

    gender_nb = models.CharField(blank=False, max_length=32, verbose_name=b'Gender', choices=[
        (b'male', b'Male'),
        (b'female', b'Female'),
        (b'nonbinary', b'Non-Binary'),

        (b'decline', b'Decline to State'),
    ])

    ethnicity = models.CharField(blank=False, max_length=128, verbose_name=b'Ethnicity', choices=[
        (b'african-american-and-black', b'African American and Black'),
        (b'american-indian-alaska-native', b'American Indian / Alaska Native'),
        (b'asian', b'Asian'),
        (b'hispanic-latinx', b'Hispanic / Latinx'),
        (b'native-hawaiian-and-pacific-islander', b'Native Hawaiian and Pacific Islander'),
        (b'southwest-asia-north-african', b'Southwest Asia / North African'),
        (b'white', b'White'),

        (b'decline', b'Decline to State'),
    ])

    age = models.CharField(blank=False, max_length=32, verbose_name=b'Age', choices=[
        (b'13-17', b'13 - 17 years old'),
        (b'18-22', b'18 - 22 years old'),
        (b'23-29', b'23 - 29 years old'),
        (b'30-49', b'30 - 49 years old'),
        (b'50-plus', b'50+ years old'),

        (b'decline', b'Decline to State'),
    ])

    education = models.CharField(blank=False, max_length=64, verbose_name=b'Highest level of education completed', choices=[
        (b'graduate', b'Graduate'),
        (b'undergraduate', b'Undergraduate'),
        (b'up-to-high-school', b'Up to High School'),

        (b'decline', b'Decline to State'),
    ])

    howheard = models.CharField(blank=False, max_length=64, verbose_name=b'How did you hear about UC San Diego Online', choices=[
        (b'social-media', b'Social Media'),
        (b'email', b'Email'),
        (b'word-of-mouth', b'Word-of-Mouth'),
        (b'print-advertisement', b'Print Advertisement'),
        (b'other', b'Other'),
    ])

    class Meta:
        verbose_name = "Additional Registration Information"
        verbose_name_plural = "Additional Registration Information"


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
