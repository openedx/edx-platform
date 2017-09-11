"""
Model form for the surveys.
"""
from itertools import chain

from django import forms
from django.utils.encoding import force_unicode

from lms.djangoapps.onboarding_survey.models import (
    OrganizationSurvey,
    InterestsSurvey,
    UserInfoSurvey
)


class UserInfoModelForm(forms.ModelForm):
    """
    Model from to be used in the first step of survey.

    This will record some basic information about the user as modeled in
    'UserInfoSurvey' model
    """
    def clean(self):
        """
        Clean the form data.
        """
        cleaned_data = super(UserInfoModelForm, self).clean()

        # if user check that his/her country/city of employment if different
        # from that of the residence, and user then enters the same country/city
        # then a validation error should be raised.
        if cleaned_data['is_country_or_city_different']:

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
            'english_prof', 'country_of_residence',
            'city_of_residence', 'is_country_or_city_different', 'country_of_employment',
            'city_of_employment'
        ]

        labels = {
            'is_country_or_city_different': 'My country or city of employment is different'
                                            ' than my country or city of residence.'
        }
        widgets = {
            'dob': forms.TextInput(attrs={'placeholder': 'Date of Birth'}),
            'country_of_employment': forms.TextInput(attrs={'placeholder': 'Country of Employment'}),
            'city_of_employment': forms.TextInput(attrs={'placeholder': 'City of Employment'}),
            'country_of_residence': forms.TextInput(attrs={'placeholder': 'Country of Residence'}),
            'city_of_residence': forms.TextInput(attrs={'placeholder': 'City of Residence'}),
            'language': forms.TextInput(attrs={'placeholder': 'Native Language'})
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'level_of_education': {
                'required': required_error.format('Level of Education'),
            },
            'english_prof': {
                'required': required_error.format('English Language Proficiency'),
            }
        }


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
        fields = ['capacity_areas', 'reason_of_interest', 'interested_communities', 'personal_goal']

        widgets = {
            'capacity_areas': forms.CheckboxSelectMultiple(),
            'interested_communities': forms.CheckboxSelectMultiple(),
            'personal_goal': forms.CheckboxSelectMultiple()
        }

        labels = {
            'capacity_areas': 'Which of these organizational capacity areas are'
                              ' interested to you? (Check all that apply)',
            'interested_communities': 'Which of these community types are interested to you? (Check all that apply)',
            'reason_of_interest': 'Why are these areas of organizational effectiveness interesting to you?',
            'personal_goal': 'Which is your most important personal goal in using the Philanthropy University platform.'
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
    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = OrganizationSurvey
        fields = ['role_in_org', 'state_mon_year', 'country', 'city', 'url', 'sector', 'level_of_op', 'focus_area',
                  'founding_year', 'total_employees', 'total_volunteers', 'total_annual_clients_or_beneficiary',
                  'total_annual_revenue_for_last_fiscal', 'partner_network']

        widgets = {
            'state_mon_year': forms.TextInput(attrs={'placeholder': 'Start Month and Year'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country of Organization Headquarters'}),
            'city': forms.TextInput(attrs={'placeholder': 'City of Organization Headquarters'}),
            'url': forms.URLInput(attrs={'placeholder': 'Organization Website'}),
            'founding_year': forms.NumberInput(attrs={'placeholder': 'Founding year'}),
            'total_annual_clients_or_beneficiary': forms.NumberInput(
                attrs={'placeholder': 'Total annual clients or beneficiaries'}),
            'total_annual_revenue_for_last_fiscal': forms.NumberInput(
                attrs={'placeholder': 'Total annual revenue for last fiscal year '})
        }

    def clean(self):
        """
        Clean the form after submission and ensure that year is 4 digit positive number.
        """
        cleaned_data = super(OrganizationInfoModelForm, self).clean()

        year = cleaned_data['founding_year']

        if len("{}".format(year)) < 4 or year < 0:
            raise forms.ValidationError("You entered an invalid year format. Please enter a valid year with 4 digits.")
