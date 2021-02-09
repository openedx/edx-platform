"""
Forms for applications app.
"""
from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.utils.translation import ugettext_lazy as _

from common.djangoapps.student.models import UserProfile
from openedx.adg.lms.applications.constants import (
    APPLICATION_REVIEW_ERROR_MSG,
    FILE_MAX_SIZE,
    MAXIMUM_AGE_LIMIT,
    MINIMUM_AGE_LIMIT
)
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile

from .helpers import validate_file_size


class ExtendedUserProfileForm(forms.Form):
    """
    Extended Profile Form for Contact Information Page
    """

    birth_day = forms.IntegerField()
    birth_month = forms.IntegerField()
    birth_year = forms.IntegerField()
    saudi_national = forms.BooleanField(required=False)

    def save(self, request=None):
        """
        Override save method to store fields in related models
        """
        data = self.cleaned_data
        user = request.user
        saudi_national = request.POST.get('saudi_national') == 'Yes'

        ExtendedUserProfile.objects.update_or_create(
            user=user,
            defaults={
                'birth_date': data.get('birth_date'),
                'saudi_national': saudi_national,
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
            except ValueError as e:  # pylint: disable=unused-variable
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
            cleaned_data['birth_date'] = birth_date
        return cleaned_data


class UserApplicationForm(forms.ModelForm):
    """
    User Application Form for Contact Information Page
    """

    class Meta:
        model = UserApplication
        fields = ['organization', 'linkedin_url', 'resume']

    def clean_resume(self):
        """
        Validate resume size is less than maximum allowed size
        """
        resume = self.cleaned_data.get('resume')
        if resume:
            error = validate_file_size(resume, FILE_MAX_SIZE)
            if error:
                raise forms.ValidationError(error)
        return resume


class UserProfileForm(forms.ModelForm):
    """
    User Profile Form for Contact Information Page
    """

    class Meta:
        model = UserProfile
        fields = ['city', 'gender', 'name', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['gender'].required = True
        self.fields['phone_number'].required = True
        self.fields['city'].disabled = True
        self.fields['name'].disabled = True


class UserApplicationAdminForm(forms.ModelForm):
    """
    Extend form for UserApplication ADG admin view.

    Extension is required to add a validation check ensuring that the application review form cannot be submitted by an
    admin unless a decision is made regarding the status of the application.
    """

    class Meta:
        model = UserApplication
        fields = '__all__'
        help_texts = {'cover_letter_file': None, 'resume': None}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserApplicationAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(UserApplicationAdminForm, self).clean()
        if 'status' not in self.request.POST:
            raise forms.ValidationError(APPLICATION_REVIEW_ERROR_MSG)


class UserApplicationCoverLetterForm(forms.ModelForm):
    """
    User Application Form for Cover Letter Page
    """

    class Meta:
        model = UserApplication
        fields = ['business_line', 'cover_letter_file', 'cover_letter']

    def clean_cover_letter_file(self):
        """
        Validate cover letter file size is less than maximum allowed size
        """
        cover_letter_file = self.cleaned_data.get('cover_letter_file')
        if cover_letter_file:
            error = validate_file_size(cover_letter_file, FILE_MAX_SIZE)
            if error:
                raise forms.ValidationError(error)
        return cover_letter_file

    def clean(self):
        """
        In addition to pre-defined validation it validates that either cover letter file or text is sent
        """
        super().clean()

        if 'cover_letter_file' in self.changed_data and self.cleaned_data.get('cover_letter'):
            self.add_error('cover_letter_file', _('Either upload a cover letter file or type text'))

    def save_form(self, post_data):
        """
        Before saving user application it checks if the cover letter file needs to be deleted if user has removed it
        """
        instance = self.save(commit=False)

        if 'cover_letter_file' in post_data and 'cover_letter' in post_data:
            instance.cover_letter_file.delete()

        instance.save()
