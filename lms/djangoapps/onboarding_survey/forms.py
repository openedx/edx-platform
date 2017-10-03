"""
Model form for the surveys.
"""
from itertools import chain

from django import forms
from django.db import models
from django.utils.encoding import force_unicode

from lms.djangoapps.onboarding_survey.models import (
    OrganizationSurvey,
    InterestsSurvey,
    UserInfoSurvey,
    ExtendedProfile,
    Organization
)


class UserInfoModelForm(forms.ModelForm):
    """
    Model from to be used in the first step of survey.

    This will record some basic information about the user as modeled in
    'UserInfoSurvey' model
    """
    def __init__(self,  *args, **kwargs):
        super(UserInfoModelForm, self).__init__( *args, **kwargs)
        self.fields['level_of_education'].empty_label = "Level of Education"
        self.fields['english_proficiency'].empty_label = "English Language Proficiency*"

    def clean(self):
        """
        Clean the form data.
        """
        cleaned_data = super(UserInfoModelForm, self).clean()

        # if user check that his/her country/city of employment if different
        # from that of the residence, and user then enters the same country/city
        # then a validation error should be raised.
        if cleaned_data['is_emp_location_different'] and cleaned_data.get('country_of_residence', None):

            if cleaned_data['country_of_employment'] == cleaned_data['country_of_residence']:
                raise forms.ValidationError(
                    "Please provide Country of Employment"
                )

            if not cleaned_data['country_of_employment']:
                raise forms.ValidationError(
                    "Please provide Country of Employment"
                )

            if not cleaned_data['city_of_employment']:
                raise forms.ValidationError(
                    "Please provide City of Employment"
                )

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = UserInfoSurvey
        fields = [
            'dob', 'level_of_education', 'language',
            'english_proficiency', 'country_of_residence',
            'city_of_residence', 'is_emp_location_different', 'country_of_employment',
            'city_of_employment'
        ]

        labels = {
            'is_emp_location_different': 'My country or city of employment is different '
                                         'than my country or city of residence.'
        }
        widgets = {
            'dob': forms.TextInput(attrs={'placeholder': 'Date of Birth'}),
            'country_of_employment': forms.TextInput(attrs={'placeholder': 'Country of Employment'}),
            'city_of_employment': forms.TextInput(attrs={'placeholder': 'City of Employment'}),
            'country_of_residence': forms.TextInput(attrs={'placeholder': 'Country of Residence*'}),
            'city_of_residence': forms.TextInput(attrs={'placeholder': 'City of Residence'}),
            'language': forms.TextInput(attrs={'placeholder': 'Native Language*'})
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'level_of_education': {
                'required': required_error.format('Level of Education'),
            },
            'english_proficiency': {
                'required': required_error.format('English Language Proficiency'),
            }
        }

    def save(self, commit=True):
        user_info_survey = super(UserInfoModelForm, self).save(commit=False)
        if not self.cleaned_data['is_emp_location_different']:
            user_info_survey.country_of_employment = ""
            user_info_survey.city_of_employment = ""

        if commit:
            user_info_survey.save()

        return user_info_survey


class RadioSelectNotNull(forms.RadioSelect):
    """
    A widget which removes the default '-----' option from RadioSelect
    """
    def get_renderer(self, name, value, attrs=None, choices=()):
        """
        Returns an instance of the renderer.
        """
        if value is None: value = ''
        # Normalize to string.
        str_value = force_unicode(value)
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        if choices[0][0] == '':
            choices.pop(0)
        return self.renderer(name, str_value, final_attrs, choices)


class InterestModelForm(forms.ModelForm):
    """
    Model from to be used in the second step of survey.

    This will record user's interests information as modeled in
    'InterestsSurvey' model.
    """
    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = InterestsSurvey
        fields = ['capacity_areas', 'reason_of_selected_interest', 'interested_communities', 'personal_goal']

        widgets = {
            'capacity_areas': forms.CheckboxSelectMultiple(),
            'interested_communities': forms.CheckboxSelectMultiple(),
            'personal_goal': forms.CheckboxSelectMultiple(),
            'reason_of_selected_interest': forms.TextInput(attrs={'placeholder': 'Enter your response here'})
        }

        labels = {
            'capacity_areas': 'Which of these organizational capacity areas are'
                              ' interesting to you? (Check all that apply)*',
            'interested_communities': 'Which of these community types are interesting to you? (Check all that apply)*',
            'reason_of_selected_interest': 'Why are these areas of organizational effectiveness interesting to you?',
            'personal_goal': 'Which is your most important personal goal in'
                             ' using the Philanthropy University platform? (Check all that apply)'
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'capacity_areas': {
                'required': required_error.format('Organization capacity area you are interested in.'),
            },
            'interested_communities': {
                'required': required_error.format('Community type you are interested in.'),
            },
            'personal_goal': {
                'required': required_error.format('Personal goal.'),
            },

        }


class OrganizationInfoModelForm(forms.ModelForm):
    """
    Model from to be used in the third step of survey.

    This will record information about user's organization as modeled in
    'OrganizationSurvey' model.
    """

    def __init__(self,  *args, **kwargs):
        super(OrganizationInfoModelForm, self).__init__( *args, **kwargs)
        self.fields['role_in_org'].empty_label = "Role in the organization"
        self.fields['sector'].empty_label = "Sector*"
        self.fields['level_of_operation'].empty_label = "Level of Operation*"
        self.fields['focus_area'].empty_label = "Focus Area*"
        self.fields['total_employees'].empty_label = "Total Employees"
        self.fields['total_volunteers'].empty_label = "Total Volunteers"
        self.fields['partner_network'].empty_label = "Partner Networks"

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = OrganizationSurvey
        fields = ['role_in_org', 'start_month_year', 'country', 'city', 'url', 'sector', 'level_of_operation',
                  'focus_area', 'founding_year', 'total_employees', 'total_volunteers', 'total_clients',
                  'total_revenue', 'partner_network']

        widgets = {
            'start_month_year': forms.TextInput(attrs={'placeholder': 'Start Month and Year'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country of Organization Headquarters*'}),
            'city': forms.TextInput(attrs={'placeholder': 'City of Organization Headquarters'}),
            'url': forms.URLInput(attrs={'placeholder': 'Organization Website(if applicable)'}),
            'founding_year': forms.NumberInput(attrs={'placeholder': 'Founding Year'}),
            'total_clients': forms.NumberInput(attrs={'placeholder': 'Total Annual Clients or Beneficiaries'}),
            'total_revenue': forms.NumberInput(attrs={'placeholder': 'Total Annual Revenue for Last Fiscal Year '})
        }

    def clean(self):
        """
        Clean the form after submission and ensure that year is 4 digit positive number.
        """
        cleaned_data = super(OrganizationInfoModelForm, self).clean()

        year = cleaned_data['founding_year']

        if year:
            if len("{}".format(year)) < 4 or year < 0 or len("{}".format(year)) > 4:
                self.add_error(
                    'founding_year',
                    "You entered an invalid year format. Please enter a valid year with 4 digits."
                )


class RegModelForm(forms.ModelForm):
    """
    Model form for extra fields in registration model
    """
    organization_name = forms.CharField(
        max_length=255,
        label='Organization Name',
        widget=forms.TextInput(
            attrs={'placeholder': 'Organization Name'}
        ),
        initial='Organization Name'
    )

    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        initial='Confirm Password'
    )

    def __init__(self, *args, **kwargs):
        super(RegModelForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = 'First Name'
        self.fields['last_name'].initial = 'Last Name'
        self.fields['org_admin_email'].initial = 'Organization Admin Email'

        self.fields['first_name'].error_messages = {
            'required': 'Please enter your First Name.',
        }

        self.fields['last_name'].error_messages = {
            'required': 'Please enter your Last Name.',
        }

        self.fields['organization_name'].error_messages = {
            'required': 'Please select your Organization.',
        }

        self.fields['confirm_password'].error_messages = {
            'required': 'Please enter your Confirm Password.',
        }

    class Meta:
        model = ExtendedProfile

        fields = (
            'confirm_password', 'first_name', 'last_name',
            'organization_name', 'is_currently_employed', 'is_poc', 'org_admin_email',
        )

        labels = {
            'is_currently_employed': "Check here if you're currently not employed.",
            'is_poc': 'Are you the Admin of your organization?',
            'org_admin_email': 'If you know who should be the Admin, please add their email address below. We\'ll send'
                               ' them an email inviting them to join the platform as the organization admin.',
        }

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'is_poc': forms.RadioSelect(choices=((1, 'Yes'), (0, 'No'))),
            'org_admin_email': forms.EmailInput(attrs=({'placeholder': 'Email'}))
        }

        serialization_options = {
            'confirm_password': {'field_type': 'password'},
            'org_admin_email': {'field_type': 'email'}
        }

        initial = {
            'first_name': 'First Name',
            'last_name': 'Last Name'
        }

    def save(self, commit=True):
        extended_profile = super(RegModelForm, self).save(commit=False)
        organization_name = self.cleaned_data['organization_name']

        is_poc = extended_profile.is_poc
        organization_to_assign, is_created = Organization.objects.get_or_create(name=organization_name)
        organization_to_assign.is_poc_exist = is_poc

        organization_to_assign.save()

        extended_profile.organization = organization_to_assign

        if commit:
            extended_profile.save()

        return extended_profile


class UpdateRegModelForm(RegModelForm):
    """
    Model form to update the registration extra fields
    """
    def __init__(self, *args, **kwargs):
        super(UpdateRegModelForm, self).__init__(*args, **kwargs)
        self.fields.pop('confirm_password')
