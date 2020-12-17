"""
Forms for applications app.
"""
from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.core.validators import FileExtensionValidator, RegexValidator
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.applications.constants import MAXIMUM_AGE_LIMIT, MINIMUM_AGE_LIMIT
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.models import UserProfile


class ContactInformationForm(forms.Form):
    """
    Application Contact Information Form
    """

    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'

    GENDER_CHOICES = (
        (MALE, _('Male')),
        (FEMALE, _('Female')),
        (OTHER, _('Prefer not to answer')),
    )
    gender = forms.ChoiceField(choices=GENDER_CHOICES, )

    phone_regex = RegexValidator(regex=r'^\+?1?\d*$', message=_('Phone number can only contain numbers.'))
    phone_number = forms.CharField(validators=[phone_regex], max_length=50, )

    birth_day = forms.IntegerField()
    birth_month = forms.IntegerField()
    birth_year = forms.IntegerField()

    organization = forms.CharField(max_length=255, required=False, )
    linkedin_url = forms.URLField(max_length=255, required=False, )
    resume = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'doc', 'jpg', 'png'])],
        help_text=_('Accepted extensions: .pdf, .doc, .jpg, .png'),
    )

    def save(self, request=None):
        """
        Override save method to store fields in related models
        """
        data = self.cleaned_data
        user = request.user
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'gender': data.get('gender'),
                'phone_number': data.get('phone_number')
            }
        )
        UserApplication.objects.update_or_create(
            user=user,
            defaults={
                'organization': data.get('organization'),
                'linkedin_url': data.get('linkedin_url'),
                'resume': data.get('resume')
            }
        )

        day = data.get('birth_day')
        month = data.get('birth_month')
        year = data.get('birth_year')
        birth_date = date(int(year), int(month), int(day))

        ExtendedUserProfile.objects.update_or_create(
            user=user,
            defaults={
                'birth_date': birth_date,
            }
        )

    def clean(self):
        """
        Verify the future birth date and age limit
        """
        cleaned_data = super().clean()
        day = cleaned_data.get('birth_day')
        month = cleaned_data.get('birth_month')
        year = cleaned_data.get('birth_year')

        if day and month and year:
            try:
                birth_date = date(int(year), int(month), int(day))
            except Exception as e:
                raise forms.ValidationError(
                    {'birth_day': [_('Please enter a valid date')]}
                )

            today = date.today()
            if birth_date >= today:
                raise forms.ValidationError(
                    {'birth_day': [_('Please enter a valid date')]}
                )
            age = relativedelta(date.today(), birth_date).years
            if age < MINIMUM_AGE_LIMIT or age > MAXIMUM_AGE_LIMIT:
                raise forms.ValidationError(
                    {'birth_day': [_('Sorry, the age limit for the program is 21-60'), ]}
                )
