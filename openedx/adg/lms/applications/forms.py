"""
Forms for applications app.
"""
from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.utils.translation import gettext_lazy as _

from common.djangoapps.student.models import UserProfile
from openedx.adg.lms.applications.constants import APPLICATION_REVIEW_ERROR_MSG, MAXIMUM_AGE_LIMIT, MINIMUM_AGE_LIMIT
from openedx.adg.lms.applications.models import MultilingualCourseGroup, UserApplication
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile

from .constants import COURSE_GROUP_PREREQ_VALIDATION_ERROR
from .helpers import validate_word_limit


class ExtendedUserProfileForm(forms.Form):
    """
    Extended Profile Form for Contact Information Page
    """

    birth_day = forms.IntegerField()
    birth_month = forms.IntegerField()
    birth_year = forms.IntegerField()
    saudi_national = forms.BooleanField(required=False)
    hear_about_omni = forms.CharField(required=False, max_length=255)

    def save(self, request=None):
        """
        Override save method to store fields in related models
        """
        data = self.cleaned_data
        user = request.user

        ExtendedUserProfile.objects.update_or_create(
            user=user,
            defaults={
                'birth_date': data.get('birth_date'),
                'saudi_national': data.get('saudi_national'),
                'hear_about_omni': data.get('hear_about_omni'),
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
                    # pylint: disable=no-member
                    {'birth_day': [_('Sorry, the age limit for the program is {min_age}-{max_age}').format(
                        min_age=MINIMUM_AGE_LIMIT, max_age=MAXIMUM_AGE_LIMIT),
                    ]}
                )
            cleaned_data['birth_date'] = birth_date
        return cleaned_data

    def clean_saudi_national(self):
        """
        Verify if the user is a saudi_national or not, and raise validation error accordingly.
        """
        saudi_national = self.cleaned_data.get('saudi_national')
        if not saudi_national:
            raise forms.ValidationError(
                _('Sorry, only a Saudi national can enter this program')
            )
        return saudi_national


class UserApplicationForm(forms.ModelForm):
    """
    User Application Form for Contact Information Page
    """

    class Meta:
        model = UserApplication
        fields = ['organization', 'linkedin_url']


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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserApplicationAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(UserApplicationAdminForm, self).clean()
        if 'status' not in self.request.POST:
            raise forms.ValidationError(APPLICATION_REVIEW_ERROR_MSG)


class BusinessLineInterestForm(forms.ModelForm):
    """
    User Application Form for Business Line & Interest Page
    """

    class Meta:
        model = UserApplication
        fields = ['business_line', 'interest_in_business']

    def clean_business_line(self):
        """
        Validates that on submit the user should have selected a business line or returns an error
        """
        business_line = self.cleaned_data.get('business_line')
        submit_button_clicked = self.data.get('submit_or_back_clicked') == 'submit'

        if submit_button_clicked and not business_line:
            raise forms.ValidationError(_('This field is required'))

        return business_line

    def clean_interest_in_business(self):
        """
        Validates that on submit the user should have added their interest in the business line or returns an error.
        Also, validates the word limit
        """
        interest_in_business = self.cleaned_data.get('interest_in_business')
        submit_button_clicked = self.data.get('submit_or_back_clicked') == 'submit'

        if submit_button_clicked and not interest_in_business:
            raise forms.ValidationError(_('This field is required'))

        validate_word_limit(interest_in_business)
        return interest_in_business


class EducationExperienceBackgroundForm(forms.ModelForm):
    """
    Form for background question in Application
    """

    class Meta:
        model = UserApplication
        fields = ('background_question',)

    def clean_background_question(self):
        """
        Validates that on next click, the user should have added their background question or returns an error.
        Also validates the word limit
        """
        background_question = self.cleaned_data.get('background_question')
        next_button_clicked = self.data.get('next_or_back_clicked') == 'next'

        if next_button_clicked and not background_question:
            raise forms.ValidationError(_('This field is required'))

        validate_word_limit(background_question)
        return background_question


class MultilingualCourseGroupForm(forms.ModelForm):
    """
    Form for MultilingualCourseGroup
    """

    class Meta:
        model = MultilingualCourseGroup
        fields = '__all__'

    def clean(self):
        """
        Add validations for when course group prerequisites are added
        """
        super().clean()

        is_program_prerequisite = self.cleaned_data['is_program_prerequisite']
        business_line_prerequisite = self.cleaned_data['business_line_prerequisite']
        is_common_business_line_prerequisite = self.cleaned_data['is_common_business_line_prerequisite']

        if is_program_prerequisite + is_common_business_line_prerequisite + bool(business_line_prerequisite) > 1:
            self.add_error('is_program_prerequisite', COURSE_GROUP_PREREQ_VALIDATION_ERROR)
