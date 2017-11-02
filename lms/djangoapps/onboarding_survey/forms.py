"""
Model form for the surveys.
"""
from itertools import chain
from django import forms
from django.utils.encoding import force_unicode
from lms.djangoapps.onboarding_survey.models import (
    OrganizationSurvey,
    InterestsSurvey,
    UserInfoSurvey,
    ExtendedProfile,
    Organization,
    OrganizationDetailSurvey,
    Currency)


class UserInfoModelForm(forms.ModelForm):
    """
    Model from to be used in the first step of survey.

    This will record some basic information about the user as modeled in
    'UserInfoSurvey' model
    """
    def __init__(self,  *args, **kwargs):
        super(UserInfoModelForm, self).__init__( *args, **kwargs)
        self.fields['level_of_education'].empty_label = None
        self.fields['english_proficiency'].empty_label = None
        self.fields['role_in_org'].empty_label = None

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
                    "Please provide Country of Employment which is difference from Country of Residence"
                )

            if not cleaned_data['country_of_employment']:
                raise forms.ValidationError(
                    "Please provide Country of Employment which is difference from Country of Residence"
                )

            if not cleaned_data['city_of_employment']:
                raise forms.ValidationError(
                    "Please provide City of Employment which is difference from City of Residence"
                )

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = UserInfoSurvey
        fields = [
            'year_of_birth', 'level_of_education', 'language',
            'english_proficiency', 'country_of_residence',
            'city_of_residence', 'is_emp_location_different', 'country_of_employment',
            'city_of_employment', 'role_in_org', 'start_month_year', 'weekly_work_hours', 'function_area'
        ]

        labels = {
            'is_emp_location_different': 'Check here if your country and/or city of employment is different'
                                         ' from your country and/or city of residence.',
            'level_of_education': 'Level of Education*',
            'english_proficiency': 'English language proficiency*',
            'role_in_org': 'Role in Organization*',
            'function_area': 'Department or function (Check all that apply.)'
        }
        widgets = {
            'year_of_birth': forms.TextInput(attrs={'placeholder': 'Year of Birth*'}),
            'country_of_employment': forms.TextInput(attrs={'placeholder': 'Country of Employment'}),
            'city_of_employment': forms.TextInput(attrs={'placeholder': 'City of Employment'}),
            'country_of_residence': forms.TextInput(attrs={'placeholder': 'Country of Residence*'}),
            'city_of_residence': forms.TextInput(attrs={'placeholder': 'City of Residence'}),
            'language': forms.TextInput(attrs={'placeholder': 'Native Language*'}),
            'level_of_education': forms.RadioSelect,
            'english_proficiency': forms.RadioSelect,
            'role_in_org': forms.RadioSelect,
            'start_month_year': forms.TextInput(attrs={'placeholder': 'Start Month and Year*'}),
            'function_area': forms.CheckboxSelectMultiple(),
            'weekly_work_hours': forms.NumberInput(attrs={'placeholder': 'Typical number of hours worked per week*'}),
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'year_of_birth': {
                'required': required_error.format('Year of birth'),
            },
            'language': {
                'required': required_error.format('Language'),
            },
            'country_of_residence': {
                'required': required_error.format('Country of residence'),
            },
            'start_month_year': {
                'required': required_error.format('Country of Start month year'),
            },
            'weekly_work_hours': {
                'required': required_error.format('Country of Weekly work hours'),
            },
            'role_in_org': {
                'required': required_error.format('Country of Role in organization'),
            },
            'level_of_education': {
                'required': required_error.format('Level of Education'),
            },
            'english_proficiency': {
                'required': required_error.format('English Language Proficiency'),
            }
        }

    def save(self, commit=True):
        user_info_survey = super(UserInfoModelForm, self).save()
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
    def __init__(self,  *args, **kwargs):
        super(InterestModelForm, self).__init__( *args, **kwargs)
        self.fields['capacity_areas'].empty_label = None

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = InterestsSurvey
        fields = ['capacity_areas', 'interested_communities', 'personal_goal']

        widgets = {
            'capacity_areas': forms.CheckboxSelectMultiple(),
            'interested_communities': forms.CheckboxSelectMultiple(),
            'personal_goal': forms.CheckboxSelectMultiple(),
        }

        labels = {
            'capacity_areas': 'Which of these organizational capacity areas are'
                              ' you most interested to learn more about',
            'interested_communities': 'Which of these community types are interesting to you? (Check all that apply)',
            'personal_goal': 'Which is your most important personal goal in'
                             ' using the Philanthropy University platform? (Check all that apply.)'
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
        self.fields['sector'].empty_label = None
        self.fields['level_of_operation'].empty_label = None
        self.fields['focus_area'].empty_label = None
        self.fields['total_employees'].empty_label = "Total Employees"
        self.fields['partner_network'].empty_label = None
        self.fields['is_org_url_exist'].required = True

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = OrganizationSurvey
        fields = ['country', 'city', 'is_org_url_exist', 'url', 'founding_year', 'sector', 'level_of_operation',
                  'focus_area', 'total_employees', 'partner_network', 'alternate_admin_email']

        widgets = {
            'country': forms.TextInput(attrs={'placeholder': 'Country of Organization Headquarters*'}),
            'city': forms.TextInput(attrs={'placeholder': 'City of Organization Headquarters'}),
            'url': forms.TextInput(attrs={'placeholder': 'Organization Website(if applicable)'}),
            'is_org_url_exist': forms.RadioSelect(choices=((1, 'Yes'), (0, 'No'))),
            'founding_year': forms.NumberInput(attrs={'placeholder': 'Founding Year'}),
            'sector': forms.RadioSelect,
            'level_of_operation': forms.RadioSelect,
            'focus_area': forms.RadioSelect,
            'partner_network': forms.CheckboxSelectMultiple,
            'alternate_admin_email': forms.EmailInput(attrs=({'placeholder': 'Organization Admin Email'}))
        }

        labels = {
            'alternate_admin_email': 'Please provide the email address for an alternative'
                                     ' Admin contact at your organization if we are unable to reach you.',
            'is_org_url_exist': 'Is org url exist*',
            'sector': 'Sector*',
            'level_of_operation': 'Level of Operation*',
            'total_employees': 'Total Employees*',
            'focus_area': 'Focus Area*',
            'country': 'Country*',
            'partner_network': 'Partner Network*',
        }

        initial = {
            "is_org_url_exist": 1
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'sector': {
                'required': required_error.format('Sector'),
            },
            'level_of_operation': {
                'required': required_error.format('Level of Operation'),
            },
            'total_employees': {
                'required': required_error.format('Total Employees'),
            },
            'focus_area': {
                'required': required_error.format('Focus Area'),
            },
            'country': {
                'required': required_error.format('Country'),
            },
            'partner_network': {
                'required': required_error.format('Partner Network'),
            },
            'is_org_url_exist': {
                'required': required_error.format('Is org url exist'),
            },

        }

    def clean_url(self):
        is_org_url_exist = int(self.data['is_org_url_exist'])
        organization_website = self.cleaned_data['url']

        if is_org_url_exist and not organization_website:
            raise forms.ValidationError("Please enter value for Organization url")

        return organization_website

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
        required=False,
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

    is_currently_employed = forms.BooleanField(
        initial=False,
        required=False,
        label="Check here if you are currently unemployed or otherwise not affiliated with an organization."
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
            'is_poc': 'Are you the Admin of your organization?',
            'org_admin_email': 'If you know who should be the Admin for [Organization name],'
                               ' please provide their email address and we will invite them to sign up.',
        }

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'is_poc': forms.RadioSelect(choices=((1, 'Yes'), (0, 'No'))),
            'org_admin_email': forms.EmailInput(attrs=({'placeholder': 'Organization Admin Email'}))
        }

        serialization_options = {
            'confirm_password': {'field_type': 'password'},
            'org_admin_email': {'field_type': 'email'}
        }

        initial = {
            'first_name': 'First Name',
            'last_name': 'Last Name'
        }

    def clean_organization_name(self):
        is_currently_unemployed = True if self.data['is_currently_employed'] == 'true' else False
        organization_name = self.cleaned_data['organization_name']

        if not is_currently_unemployed and not organization_name:
            raise forms.ValidationError("Please enter organization name")

        return organization_name

    def save(self, user=None, commit=True):
        extended_profile = super(RegModelForm, self).save(commit=False)
        organization_name = self.cleaned_data['organization_name']

        is_poc = extended_profile.is_poc
        organization_to_assign, is_created = Organization.objects.get_or_create(name=organization_name)
        prev_org = extended_profile.organization

        if user and is_poc:
            organization_to_assign.admin = user
            extended_profile.is_poc = True

            organization_to_assign.save()

        if prev_org:
            if organization_to_assign.name != prev_org.name:
                prev_org.admin = None
                prev_org.save()

        extended_profile.organization = organization_to_assign
        extended_profile.user = user

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


class OrganizationDetailModelForm(forms.ModelForm):

    currency_input = forms.CharField(
        max_length=255,
        label='Local currency code*',
        widget=forms.TextInput(
            attrs={'placeholder': 'Local currency code*'}
        ),
        required=False
    )

    def __init__(self,  *args, **kwargs):
        super(OrganizationDetailModelForm, self).__init__(*args, **kwargs)
        self.fields['can_provide_info'].empty_label = None
        self.fields['info_accuracy'].empty_label = None
        self.fields['can_provide_info'].required = True

        self.fields['info_accuracy'].required = False
        self.fields['last_fiscal_year_end_date'].required = False
        self.fields['total_clients'].required = False
        self.fields['total_employees'].required = False
        self.fields['currency_input'].required = False
        self.fields['total_revenue'].required = False
        self.fields['total_expenses'].required = False
        self.fields['total_program_expenses'].required = False

    class Meta:
        model = OrganizationDetailSurvey

        fields = [
            'can_provide_info', 'info_accuracy', 'last_fiscal_year_end_date', 'total_clients',
            'total_employees', 'currency_input', 'total_revenue', 'total_expenses', 'total_program_expenses'
        ]

        widgets = {
            'can_provide_info': forms.RadioSelect,
            'info_accuracy': RadioSelectNotNull,
            'last_fiscal_year_end_date': forms.TextInput(attrs={'placeholder': 'End date of last fiscal year*'}),
            'total_clients': forms.NumberInput(
                attrs={'placeholder': 'Total Annual Clients or Direct Beneficiaries for Last Fiscal Year*'}
            ),
            'total_employees': forms.NumberInput(attrs={'placeholder': 'Total employees at end of last fiscal year*'}),

            'total_revenue': forms.NumberInput(
                attrs={'placeholder': 'Total Annual Revenue for Last Fiscal Year (local currency)*'}
            ),
            'total_expenses': forms.NumberInput(
                attrs={'placeholder': 'Total Annual Expenses for Last Fiscal Year (local currency)*'}
            ),
            'total_program_expenses': forms.NumberInput(
                attrs={'placeholder': 'Total Annual Program Expenses for Last Fiscal Year (local currency)*'}
            )
        }

        labels = {
            'can_provide_info': 'Are you able to provide the information requested below?',
            'info_accuracy': 'Is the information you will provide on this page estimated or actual?'
        }

    def clean_info_accuracy(self):
        can_provide_info = int(self.data['can_provide_info'])
        info_accuracy = self.cleaned_data['info_accuracy']

        if can_provide_info and not info_accuracy:
            raise forms.ValidationError("Please select an option for Estimated or Actual Information")

        return info_accuracy

    def clean_last_fiscal_year_end_date(self):
        can_provide_info = int(self.data['can_provide_info'])
        last_fiscal_year_end_date = self.cleaned_data['last_fiscal_year_end_date']

        if can_provide_info and not last_fiscal_year_end_date:
            raise forms.ValidationError("Please enter your End date for last fiscal year")

        return last_fiscal_year_end_date

    def clean_total_clients(self):
        can_provide_info = int(self.data['can_provide_info'])
        total_clients = self.cleaned_data['total_clients']

        if can_provide_info and not total_clients:
            raise forms.ValidationError("Please enter your Total client")

        return total_clients

    def clean_total_employees(self):
        can_provide_info = int(self.data['can_provide_info'])
        total_employees = self.cleaned_data['total_employees']

        if can_provide_info and not total_employees:
            raise forms.ValidationError("Please enter your Total employees")

        return total_employees

    def clean_total_revenue(self):
        can_provide_info = int(self.data['can_provide_info'])
        total_revenue = self.cleaned_data['total_revenue']

        if can_provide_info and not total_revenue:
            raise forms.ValidationError("Please enter your Total revenue")

        return total_revenue

    def clean_total_expenses(self):
        can_provide_info = int(self.data['can_provide_info'])
        total_expenses = self.cleaned_data['total_expenses']

        if can_provide_info and not total_expenses:
            raise forms.ValidationError("Please enter your Total expenses")

        return total_expenses

    def clean_total_program_expenses(self):
        can_provide_info = int(self.data['can_provide_info'])
        total_program_expenses = self.cleaned_data['total_program_expenses']

        if can_provide_info and not total_program_expenses:
            raise forms.ValidationError("Please enter your Total program expense")

        return total_program_expenses

    def save(self, user=None, commit=True):
        org_detail = super(OrganizationDetailModelForm, self).save(commit=False)
        if user:
            org_detail.user = user

        can_provide_info = int(self.data['can_provide_info'])
        if can_provide_info:
            org_detail.currency = Currency.objects.filter(alphabetic_code=self.cleaned_data['currency_input']).first()

        if commit:
            org_detail.save()

        return org_detail