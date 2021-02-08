"""
Model form for the surveys.
"""
import json
import logging
import os
from datetime import datetime

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy, ugettext_noop
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.onboarding.email_utils import send_admin_activation_email
from lms.djangoapps.onboarding.helpers import COUNTRIES, LANGUAGES, get_country_iso
from lms.djangoapps.onboarding.models import (
    Currency,
    EducationLevel,
    EmailPreference,
    EnglishProficiency,
    FocusArea,
    GranteeOptIn,
    OperationLevel,
    Organization,
    OrganizationAdminHashKeys,
    OrganizationMetric,
    OrganizationPartner,
    OrgSector,
    PartnerNetwork,
    RoleInsideOrg,
    TotalEmployee,
    UserExtendedProfile
)
from lms.djangoapps.philu_overrides.helpers import save_user_partner_network_consent
from openedx.features.ondemand_email_preferences.models import OnDemandEmailPreferences

NO_OPTION_SELECT_ERROR = 'Please select an option for {}'
EMPTY_FIELD_ERROR = 'Please enter your {}'
log = logging.getLogger("edx.onboarding")


def get_onboarding_autosuggesion_data(file_name):
    """
    Receives a json file name and return data related to autocomplete fields in
    onboarding survey.
    """

    curr_dir = os.path.dirname(__file__)
    file_path = "{}/{}".format('data', file_name)
    json_file = open(os.path.join(curr_dir, file_path))
    data = json.load(json_file)
    return data


class BaseOnboardingModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', kwargs.get('label_suffix', '').replace(":", ""))
        kwargs.setdefault('use_required_attribute', False)
        super(BaseOnboardingModelForm, self).__init__(*args, **kwargs)


class BaseOnboardingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', kwargs.get('label_suffix', '').replace(":", ""))
        super(BaseOnboardingForm, self).__init__(*args, **kwargs)


class UserInfoModelForm(BaseOnboardingModelForm):
    """
    Model from to be used in the first step of survey.

    This will record some basic information about the user as modeled in
    'UserInfoSurvey' model
    """
    GENDER_CHOICES = (
        ('m', ugettext_noop('Male')),
        ('f', ugettext_noop('Female')),
        # Translators: 'Other' refers to the student's gender
        ('o', ugettext_noop("I'd rather not say")),
        ('nl', ugettext_noop('Not listed')),
    )

    NO_SELECT_CHOICE = [('', ugettext_noop('- Select -'))]

    IS_POC_CHOICES = (
        (1, ugettext_noop('Yes')),
        (0, ugettext_noop('No'))
    )

    year_of_birth = forms.IntegerField(
        label="Year of Birth",
        label_suffix="*",
        validators=[
            MinValueValidator(1900, message=ugettext_noop('Ensure year of birth is greater than or equal to 1900')),
            MaxValueValidator(
                datetime.now().year, message=ugettext_noop('Ensure year of birth is less than or equal to {}'.format(
                    datetime.now().year
                ))
            )
        ],
        error_messages={
            'required': EMPTY_FIELD_ERROR.format(ugettext_noop("Year of birth")),
        }
    )
    gender = forms.ChoiceField(label=ugettext_noop('Gender'), required=False, label_suffix="*", choices=GENDER_CHOICES,
                               widget=forms.RadioSelect)

    language = forms.CharField(label=ugettext_noop('Native Language'), label_suffix="*", required=True,
                               error_messages={"required": ugettext_noop(EMPTY_FIELD_ERROR.format('Language'))},
                               widget=forms.HiddenInput)
    country = forms.CharField(
        label="Country of Residence",
        label_suffix="*",
        widget=forms.HiddenInput,
        error_messages={
            "required": ugettext_noop(EMPTY_FIELD_ERROR.format("Country of Residence"))
        }
    )

    city = forms.CharField(label=ugettext_noop('City of Residence'), required=False, widget=forms.HiddenInput)
    is_emp_location_different = forms.BooleanField(label=ugettext_noop('Check here if your country and/or city of '
                                                                       'employment is different from your country '
                                                                       'and/or city of residence.'),
                                                   required=False)
    level_of_education = forms.ChoiceField(
        label=ugettext_noop('Level of Education'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Level of Education'))
        },
        required=True
    )
    english_proficiency = forms.ChoiceField(
        label=ugettext_noop('English Language Proficiency'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('English Language Proficiency'))
        }
    )
    role_in_org = forms.ChoiceField(
        label=ugettext_noop('Role in the Organization'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Role in the Organization'))
        }
    )

    organization_name = forms.CharField(
        max_length=255,
        label=ugettext_noop('Organization Name'),
        label_suffix="*",
        help_text=ugettext_noop("You can choose an organization from the auto-suggestion list or add a new one by "
                                "entering the name and clicking the OK button."),
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': ugettext_noop('Organization Name')}
        ),
        initial=ugettext_noop('Organization Name')
    )

    is_currently_employed = forms.BooleanField(
        initial=False,
        required=False,
        label=ugettext_noop('Check here if you are currently unemployed or otherwise not affiliated with an '
                            'organization.')
    )

    is_poc = forms.ChoiceField(label=ugettext_noop('Will you be the Administrator of your organization on our '
                                                   'website?'),
                               help_text=ugettext_noop("Your organization's Administrator is responsible for "
                                                       "maintaining your organization's profile and inviting learners "
                                                       "from your organization to the Philanthropy University platform."
                                                       " An Administrator should be the most senior person in your "
                                                       "organization responsible for organizational capacity building "
                                                       "and learning. In a small organization with few employees, "
                                                       "the Administrator might be the Executive Director or Chief "
                                                       "Executive. In a larger organization, the Administrator might "
                                                       "be the director or manager responsible for staff learning "
                                                       "and development and organizational capacity development."),
                               choices=IS_POC_CHOICES,
                               widget=forms.RadioSelect)

    org_admin_email = forms.CharField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Organization Admin email'}))

    def __init__(self, *args, **kwargs):
        super(UserInfoModelForm, self).__init__(*args, **kwargs)

        LEVEL_OF_EDUCATION_CHOICES = self.NO_SELECT_CHOICE + [(el.code, el.label)
                                                              for el in EducationLevel.objects.all()]
        ENGLISH_PROFICIENCY_CHOICES = self.NO_SELECT_CHOICE + [(ep.code, ep.label)
                                                               for ep in EnglishProficiency.objects.all()]
        ROLE_IN_ORG_CHOICES = self.NO_SELECT_CHOICE + [(r.code, r.label)
                                                       for r in RoleInsideOrg.objects.all()]

        self.fields['level_of_education'].choices = LEVEL_OF_EDUCATION_CHOICES
        self.fields['english_proficiency'].choices = ENGLISH_PROFICIENCY_CHOICES
        self.fields['role_in_org'].choices = ROLE_IN_ORG_CHOICES

        self.fields['organization_name'].error_messages = {
            'required': ugettext_noop('Please select your Organization.'),
        }

        self.fields['country_of_employment'].required = False
        self.fields['city_of_employment'].required = False

        self.fields['role_in_org'].required = False
        self.fields['start_month_year'].required = False
        self.fields['hours_per_week'].required = False

    def clean(self):
        if self.errors.get('function_areas'):
            del self.errors['function_areas']

    def clean_gender(self):

        not_listed_gender = self.data.get('not_listed_gender', None)
        gender = self.cleaned_data['gender']

        if not gender:
            raise forms.ValidationError('Please select Gender.')

        if gender == 'nl' and not not_listed_gender:
            raise forms.ValidationError('Please specify Gender.')

        return gender

    def clean_country(self):
        all_countries = COUNTRIES.values()
        country = self.cleaned_data['country']

        if country in all_countries:
            return country

        raise forms.ValidationError(ugettext_noop('Please select country of residence.'))

    def clean_language(self):
        submitted_language = self.cleaned_data['language']

        if submitted_language in LANGUAGES:
            return submitted_language

        raise forms.ValidationError(ugettext_noop('Please select language.'))

    def clean_organization_name(self):
        organization_name = self.data.get('organization_name')

        if not self.data.get('is_currently_employed') and not organization_name:
            raise forms.ValidationError(ugettext_noop('Please enter Organization Name.'))

        return organization_name

    def clean_role_in_org(self):
        if self.data.get('organization_name'):
            if not self.cleaned_data['role_in_org']:
                raise forms.ValidationError(ugettext_noop(NO_OPTION_SELECT_ERROR.format(
                    'Role in the Organization')))
        return self.cleaned_data['role_in_org']

    def clean_start_month_year(self):
        if self.data.get('organization_name'):
            if not self.cleaned_data['start_month_year']:
                raise forms.ValidationError(ugettext_noop("Please enter a valid start month/year"))

            start_month_year = datetime.strptime(
                self.cleaned_data['start_month_year'],
                '%m/%Y')
            if start_month_year > datetime.now():
                raise forms.ValidationError(ugettext_noop("Please enter a valid start month/year"))

        return self.cleaned_data['start_month_year']

    def clean_hours_per_week(self):
        if self.data.get('organization_name'):
            if not self.cleaned_data['hours_per_week']:
                raise forms.ValidationError(
                    ugettext_noop(EMPTY_FIELD_ERROR.format('Hours per week')))
        return self.cleaned_data['hours_per_week']

    def clean_org_admin_email(self):
        org_admin_email = self.cleaned_data['org_admin_email']

        already_an_admin = Organization.objects.filter(admin__email=org_admin_email).first()
        if already_an_admin:
            raise forms.ValidationError(ugettext_noop('%s is already admin of organization "%s"'
                                                      % (org_admin_email, already_an_admin.label)))

        already_suggested_as_admin = OrganizationAdminHashKeys.objects.filter(
            suggested_admin_email=org_admin_email, is_hash_consumed=False).first()
        if already_suggested_as_admin:
            raise forms.ValidationError(ugettext_noop('%s is already suggested as admin of "%s" organization'
                                                      % (org_admin_email,
                                                         already_suggested_as_admin.organization.label)))

        return org_admin_email

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = UserExtendedProfile
        fields = [
            'year_of_birth', 'gender', 'not_listed_gender', 'not_listed_gender', 'level_of_education', 'language',
            'english_proficiency', 'country', 'city', 'is_emp_location_different', 'country_of_employment',
            'city_of_employment', 'role_in_org', 'start_month_year', 'hours_per_week', 'organization_name',
            'is_currently_employed', 'is_poc', 'org_admin_email', 'function_areas'
        ]

        labels = {
            'is_emp_location_different': ugettext_noop(
                'Check here if your country and/or city of employment is different'
                ' from your country and/or city of residence.'),
            'start_month_year': ugettext_noop('Start Month and Year*'),
            'country_of_employment': ugettext_noop('Country of Employment'),
            'city_of_employment': ugettext_noop('City of Employment'),
            'role_in_org': ugettext_noop('Role in Organization*'),
            'function_areas': ugettext_lazy('Department or Function (Check all that apply.)')
        }
        widgets = {
            'year_of_birth': forms.TextInput,
            'not_listed_gender': forms.TextInput(attrs={'placeholder': ugettext_noop('Identify your gender here')}),
            'country_of_employment': forms.HiddenInput,
            'city_of_employment': forms.HiddenInput,
            'start_month_year': forms.TextInput(attrs={'placeholder': 'MM/YYYY'}),
            'hours_per_week': forms.NumberInput(attrs={'max': 168})
        }

        error_messages = {
            "hours_per_week": {
                'required': EMPTY_FIELD_ERROR.format(ugettext_noop('Typical Number of Hours Worked per Week'))
            },
            'start_month_year': {
                'required': EMPTY_FIELD_ERROR.format(ugettext_noop('Start Month and Year')),
            }
        }

        serialization_options = {
            'org_admin_email': {'field_type': 'email'}
        }

    def save(self, request, commit=True):
        user_info_survey = super(UserInfoModelForm, self).save(commit=False)

        userprofile = user_info_survey.user.profile
        userprofile.year_of_birth = self.cleaned_data['year_of_birth']
        userprofile.language = self.cleaned_data['language']

        userprofile.country = get_country_iso(request.POST['country'])
        userprofile.city = self.cleaned_data['city']
        userprofile.level_of_education = self.cleaned_data['level_of_education']
        if self.cleaned_data['gender']:
            userprofile.gender = self.cleaned_data['gender']
        userprofile.save()

        user_info_survey.country_of_employment = get_country_iso(
            request.POST.get('country_of_employment'))
        user_info_survey.city_of_employment = self.cleaned_data['city_of_employment']

        is_currently_unemployed = self.cleaned_data['is_currently_employed']

        user = user_info_survey.user
        first_name = user.first_name
        last_name = user.last_name

        if not is_currently_unemployed:
            organization_name = self.cleaned_data.get('organization_name', '').strip()
            is_poc = self.cleaned_data['is_poc']
            org_admin_email = self.cleaned_data['org_admin_email']

        if not is_currently_unemployed and organization_name:
            organization_to_assign = Organization.objects.filter(label__iexact=organization_name).first()
            if not organization_to_assign:
                organization_to_assign = Organization.objects.create(label=organization_name)

            prev_org = user_info_survey.organization
            user_info_survey.organization = organization_to_assign
            user_info_survey.is_first_learner = organization_to_assign.can_join_as_first_learner(exclude_user=user)

            # Reset organizations under my administrations if i updated my organization & ask for org details
            if not prev_org == organization_to_assign:
                Organization.objects.filter(admin=user).update(admin=None)
                user_info_survey.is_organization_metrics_submitted = False

            if user and is_poc == '1':
                organization_to_assign.unclaimed_org_admin_email = None
                organization_to_assign.admin = user
                user_info_survey.organization = organization_to_assign

            if not is_poc == '1' and org_admin_email:
                try:
                    hash_key = OrganizationAdminHashKeys.assign_hash(organization_to_assign, user, org_admin_email)
                    org_id = user_info_survey.organization_id
                    org_name = user_info_survey.organization.label
                    organization_to_assign.unclaimed_org_admin_email = org_admin_email
                    claimed_by_name = "{first_name} {last_name}".format(first_name=first_name, last_name=last_name)
                    claimed_by_email = self.data["email"]
                    send_admin_activation_email(first_name, org_id, org_name, claimed_by_name,
                                                claimed_by_email, org_admin_email, hash_key)
                    user_info_survey.organization = organization_to_assign
                except Exception as ex:
                    log.info(ex.args)
                    pass

            # If user wants to remove h/er-self as admin from any organization.
            if not is_poc == '1':
                if organization_to_assign.admin == user:
                    organization_to_assign.admin = None
                    user_info_survey.organization = organization_to_assign

        elif is_currently_unemployed:
            if user_info_survey.organization and user_info_survey.organization.admin == user:
                user_info_survey.organization.admin = None
                user_info_survey.organization.save()

            if user_info_survey.is_first_learner:
                user_info_survey.is_first_learner = False

            user_info_survey.organization = None
            user_info_survey.start_month_year = None
            user_info_survey.hours_per_week = 0
            user_info_survey.role_in_org = None
            del user_info_survey.user.extended_profile.function_areas[:]
            user_info_survey.is_organization_metrics_submitted = False

        if commit:
            user_info_survey.save()

        partners_opt_in = request.POST.get('partners_opt_in')
        save_user_partner_network_consent(user, partners_opt_in)

        return user_info_survey


class RadioSelectNotNull(forms.RadioSelect):
    """
    A widget which removes the default '-----' option from RadioSelect
    """

    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget."""
        if self.choices[0][0] == '':
            self.choices.pop(0)
        return super(RadioSelectNotNull, self).optgroups(name, value, attrs)


class InterestsModelForm(BaseOnboardingModelForm):
    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = UserExtendedProfile
        fields = [
            'interests', 'learners_related', 'goals', 'hear_about_philanthropyu'
        ]

        labels = {
            'interests': ugettext_lazy(
                'Which of these areas of organizational effectiveness are you'
                ' most interested to learn more about? (Check all that apply.)'
            ),
            'learners_related': ugettext_lazy(
                'Which types of other Philanthropy University learners are '
                'interesting to you? (Check all that apply.)'
            ),
            'goals': ugettext_lazy(
                'What is your most important personal goal in joining '
                'Philanthropy University? (Check all that apply.)'
            ),
            'hear_about_philanthropyu': ugettext_lazy(
                'How did you hear about Philanthropy University? (Choose one. '
                'If more than one applies, please choose the source that most '
                'strongly influenced you to visit the website.)'
            )
        }

    def save(self, request, commit=True):
        user_extended_profile = super(InterestsModelForm, self).save(commit=False)
        user_extended_profile.is_interests_data_submitted = True

        if commit:
            user_extended_profile.save()

        return user_extended_profile


class OrganizationInfoForm(BaseOnboardingModelForm):
    """
    Model from to be used in the third step of survey.

    This will record information about user's organization as modeled in
    'OrganizationSurvey' model.
    """

    NO_SELECT_CHOICE = [('', '- Select -')]

    is_org_url_exist = forms.ChoiceField(
        label=ugettext_noop('Does your organization have a website?'),
        choices=((1, ugettext_noop('Yes')), (0, ugettext_noop('No'))),
        label_suffix='*',
        widget=forms.RadioSelect,
        initial=1,
        help_text=ugettext_noop(
            "If your organization does not have its own website, "
            "but it does have a page on another platform like "
            "Facebook or WordPress, please answer Yes here and "
            "give the address for this page."
        ),
        error_messages={
            'required': ugettext_noop('Please select an option for "Does your organization have a webpage?"')
        }
    )

    org_type = forms.ChoiceField(
        label=ugettext_noop('Organization Type'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Organization Type'))
        }
    )

    level_of_operation = forms.ChoiceField(
        label=ugettext_noop('Level of Operation'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Level of Operation'))
        }
    )

    focus_area = forms.ChoiceField(
        label=ugettext_noop('Primary Focus Area'),
        label_suffix='*',
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Primary Focus Areas'))
        }
    )

    total_employees = forms.ChoiceField(
        label=ugettext_noop('Total Employees'),
        label_suffix='*',
        help_text="An employee is a member of your staff who is paid for their work. "
                  "A staff member working full-time counts as 1 employee; a staff "
                  "member working half-time counts as 0.5 of an employee. Please "
                  "include yourself in your organization's employee count.",
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format('Total Employees'))
        }
    )

    partner_networks = forms.ChoiceField(
        label=ugettext_noop(
            "Is your organization currently working with any of "
            "Philanthropy University's partners? "
            "(Check all that apply.)"
        ),
        help_text=ugettext_noop(
            "Philanthropy University works in partnership with a "
            "number of organizations to improve the "
            "effectiveness of local organizations they fund and/or"
            " partner with to deliver programs. If you were asked "
            "to join Philanthropy University by one of your "
            "partners or funders and that organization appears in "
            "this list, please select it."
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        error_messages={
            'required': ugettext_noop(NO_OPTION_SELECT_ERROR.format("Partner's"))
        }
    )

    def __init__(self, *args, **kwargs):
        super(OrganizationInfoForm, self).__init__(*args, **kwargs)

        ORG_TYPE_CHOICES = self.NO_SELECT_CHOICE + [(os.code, os.label) for os in OrgSector.objects.all()]
        OPERATION_LEVEL_CHOICES = self.NO_SELECT_CHOICE + [(ol.code, ol.label)
                                                           for ol in OperationLevel.objects.all()]
        FOCUS_AREA_CHOICES = self.NO_SELECT_CHOICE + [(fa.code, fa.label) for fa in FocusArea.objects.all()]
        TOTAL_EMPLOYEES_CHOICES = self.NO_SELECT_CHOICE + [(ep.code, ep.label)
                                                           for ep in TotalEmployee.objects.all()]
        PARTNER_NETWORK_CHOICES = [(pn.code, pn.label) for pn in PartnerNetwork.objects.all()]

        self.fields['org_type'].choices = ORG_TYPE_CHOICES
        self.fields['level_of_operation'].choices = OPERATION_LEVEL_CHOICES
        self.fields['focus_area'].choices = FOCUS_AREA_CHOICES
        self.fields['total_employees'].choices = TOTAL_EMPLOYEES_CHOICES
        self.fields['partner_networks'].choices = PARTNER_NETWORK_CHOICES

        self.fields['city'].required = False
        self.fields['founding_year'].required = True

    class Meta:
        """
        The meta class used to customize the default behaviour of form fields
        """
        model = Organization
        fields = ['country', 'city', 'is_org_url_exist', 'url', 'founding_year', 'focus_area',
                  'org_type', 'level_of_operation', 'total_employees', 'alternate_admin_email', 'partner_networks']

        widgets = {
            'country': forms.HiddenInput,
            'city': forms.HiddenInput,
            'url': forms.TextInput,
            'founding_year': forms.NumberInput,
            'alternate_admin_email': forms.TextInput,
            'registration_number': forms.TextInput
        }

        labels = {
            'country': ugettext_noop('Country of Organization Headquarters*'),
            'city': ugettext_noop('City of Organization Headquarters'),
            'founding_year': ugettext_noop('Founding Year*'),
            'is_org_url_exist': ugettext_noop('Does your organization have a webpage?'),
            'url': ugettext_noop('Website Address*'),
            'alternate_admin_email': ugettext_noop('Please provide the email address for an alternative Administrator '
                                                   'contact at your organization if we are unable to reach you.'),
        }

        required_error = 'Please select an option for {}'

        error_messages = {
            'founding_year': {
                'required': ugettext_noop(EMPTY_FIELD_ERROR.format('Founding Year')),
            },
            'country': {
                'required': ugettext_noop(EMPTY_FIELD_ERROR.format('Country of Organization Headquarters')),
            }
        }

        help_texts = {
            "founding_year": ugettext_noop("Founding year is the year that your organization was started. This may be "
                                           "before your organization was legally registered."),
        }

    def clean_country(self):
        all_countries = COUNTRIES.values()
        country = self.cleaned_data['country']

        if country in all_countries:
            return country

        raise forms.ValidationError(ugettext_noop('Please select country of Organization Headquarters.'))

    def clean_url(self):
        is_org_url_exist = int(self.data.get('is_org_url_exist')) if self.data.get('is_org_url_exist') else None
        org_website = self.cleaned_data.get('url', '')
        org_website = org_website and org_website.replace('http://', 'https://', 1)

        if is_org_url_exist and not org_website:
            raise forms.ValidationError(EMPTY_FIELD_ERROR.format(ugettext_noop('Organization Website')))

        elif not is_org_url_exist:
            org_website = ''

        return org_website

    def clean(self):
        """
        Clean the form after submission and ensure that year is 4 digit positive number.
        """
        cleaned_data = super(OrganizationInfoForm, self).clean()

        if self.errors.get('partner_networks'):
            del self.errors['partner_networks']

        year = cleaned_data.get('founding_year', '')

        if year:
            if len("{}".format(year)) < 4 or year < 0 or len("{}".format(year)) > 4:
                self.add_error(
                    'founding_year',
                    ugettext_noop('You entered an invalid year format. Please enter a valid year with 4 digits.')
                )

    def save(self, request, commit=True):
        organization = super(OrganizationInfoForm, self).save(commit=False)
        organization.country = get_country_iso(self.cleaned_data['country'])

        if commit:
            organization.save()

        partners = request.POST.getlist('partner_networks')
        removed_partners = request.POST.get('removed_org_partners', '').split(",")

        if partners or removed_partners:
            OrganizationPartner.update_organization_partners(organization, partners, removed_partners)

        # Create user GranteeOptIn object if user has agreed to opt in and partner is selected.
        partners_opt_in = list(set(request.POST.get('partners_opt_in', '').split(",")) & set(partners))
        for p in partners_opt_in:
            # Get organization partner who is still affiliated
            organization_partner = organization.organization_partners.filter(
                partner=p, end_date__gt=datetime.utcnow()
            ).first()
            if organization_partner:
                GranteeOptIn.objects.create(
                    agreed=True,
                    organization_partner=organization_partner,
                    user=request.user
                )


class RegModelForm(BaseOnboardingModelForm):
    """
    Model form for extra fields in registration model
    """

    first_name = forms.CharField(
        label=ugettext_noop('First Name'),
        label_suffix="*",
        widget=forms.TextInput(
            attrs={'placeholder': ugettext_noop('First Name')}
        )
    )

    last_name = forms.CharField(
        label=ugettext_noop('Last Name'),
        label_suffix="*",
        widget=forms.TextInput(
            attrs={'placeholder': ugettext_noop('Last Name')}
        )
    )

    confirm_password = forms.CharField(
        label=ugettext_noop('Confirm Password'),
        widget=forms.PasswordInput
    )

    opt_in = forms.BooleanField(label=ugettext_noop('Check here if you agree to receive emails from Philanthropy '
                                                    'University with details about <strong>unique funding opportunities'
                                                    ', free regional events and new course and community programming'
                                                    '</strong>! If you decide later you are no longer interested, you '
                                                    'can unsubscribe from these at anytime'), required=False)

    def __init__(self, *args, **kwargs):
        super(RegModelForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].error_messages = {
            'required': ugettext_noop('Please enter your First Name.'),
        }

        self.fields['last_name'].error_messages = {
            'required': ugettext_noop('Please enter your Last Name.'),
        }

        self.fields['confirm_password'].error_messages = {
            'required': ugettext_noop('Please enter your Confirm Password.'),
        }

    class Meta:
        model = UserExtendedProfile

        fields = (
            'confirm_password', 'first_name', 'last_name',
        )

        labels = {
            'username': 'Public Username*',

        }

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'})
        }

        serialization_options = {
            'confirm_password': {'field_type': 'password'},
            'org_admin_email': {'field_type': 'email'}
        }

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'].strip()
        if len(first_name) <= 0:
            raise forms.ValidationError("Please enter valid First Name.")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name'].strip()
        if len(last_name) <= 0:
            raise forms.ValidationError("Please enter valid Last Name.")

        return last_name

    def save_email_preferences(self, user, opt_in):
        user_email_preferences, created = EmailPreference.objects.get_or_create(user=user)
        if (not user_email_preferences.opt_in and opt_in in ['yes', 'no']) or (
                user_email_preferences.opt_in in ['yes', 'no']):
            user_email_preferences.opt_in = opt_in
            user_email_preferences.save()

    def save(self, user=None, commit=True, is_alquity_user=False):
        opt_in = self.cleaned_data['opt_in']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        extended_profile = UserExtendedProfile.objects.create(user=user)
        extended_profile.is_alquity_user = is_alquity_user

        user.first_name = first_name
        user.last_name = last_name

        if commit:
            extended_profile.save()

        opt_in = "yes" if opt_in else "no"
        self.save_email_preferences(user, opt_in)

        return extended_profile


class UpdateRegModelForm(RegModelForm):
    """
    Model form to update the registration extra fields
    """
    OPT_IN_CHOICES = (
        ('yes', ugettext_noop('Yes, send me special offers')),
        ('no', ugettext_noop("No, don't send me special offers"))
    )

    opt_in = forms.ChoiceField(label=ugettext_noop('Do you want to hear from us about <strong>*unique funding '
                                                   'opportunities, free regional events, and new course and community '
                                                   'programming?*</strong> If so, please check "Yes". If not, please '
                                                   'check "No".'),
                               required=False, label_suffix="*", choices=OPT_IN_CHOICES, widget=forms.RadioSelect)

    ON_DEMAND_EMAIL_CHOICES = (
        (True, ugettext_noop('Send all reminder emails (recommended)')),
        (False, ugettext_noop('Don\'t send any reminder emails'))
    )

    on_demand_emails_enable = forms.ChoiceField(
        label='If you wish to change the reminder email preferences for any of the on-demand '
              'courses that you\'re enrolled in, select the course from the drop-down below '
              'and choose your desired email preferences.',
        choices=ON_DEMAND_EMAIL_CHOICES,
        widget=forms.RadioSelect,
        required=False
    )

    on_demand_courses = forms.CharField(
        label=ugettext_noop('Select course'),
        widget=forms.Select(choices=()),
        required=False
    )

    def __init__(self, on_demand_courses, is_nudges_enable, *args, **kwargs):
        super(UpdateRegModelForm, self).__init__(*args, **kwargs)
        self.fields.pop('confirm_password')
        self.fields['on_demand_courses'].widget.choices = on_demand_courses
        self.fields['on_demand_emails_enable'].initial = is_nudges_enable

    def save(self, user=None, commit=True):
        opt_in = self.cleaned_data['opt_in']
        on_demand_course = self.cleaned_data['on_demand_courses']
        on_demand_emails_enable = self.cleaned_data['on_demand_emails_enable']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        extended_profile = UserExtendedProfile.objects.get(user=user)

        user.first_name = first_name
        user.last_name = last_name

        if commit:
            user.save()
            extended_profile.save()

        self.save_email_preferences(user, opt_in)
        self.save_on_demand_email_preferences(user, on_demand_course, on_demand_emails_enable)

        return extended_profile

    def save_on_demand_email_preferences(self, user, on_demand_course, on_demand_emails_enable):
        if len(on_demand_course) > 0:
            map_bool = {
                'True': True,
                'False': False
            }

            on_demand_email_preferences, created = OnDemandEmailPreferences.objects.get_or_create(
                user=user, course_id=CourseKey.from_string(on_demand_course))
            on_demand_email_preferences.is_enabled = map_bool[on_demand_emails_enable]
            on_demand_email_preferences.save()


class OrganizationMetricModelForm(BaseOnboardingModelForm):
    can_provide_info = forms.ChoiceField(
        label=ugettext_noop('Are you able to provide information requested below?'),
        choices=((1, ugettext_noop('Yes')), (0, ugettext_noop('No'))),
        label_suffix='*',
        widget=forms.RadioSelect,
        initial=1,
        error_messages={
            'required': ugettext_noop('Please select an option for Are you able to provide information')
        }
    )
    effective_date = forms.DateField(input_formats=['%m/%d/%Y'],
                                     required=False,
                                     label=ugettext_noop('End Date of Last Fiscal Year'),
                                     help_text=ugettext_noop("The fiscal year is the period that an organization uses "
                                                             "for accounting  purposes and preparing financial "
                                                             "statements. A fiscal year may or may not be the same"
                                                             " as a calendar year. If the information you are "
                                                             "giving below is for the last 12 months, please enter "
                                                             "today's date."),
                                     label_suffix='*')
    registration_number = forms.CharField(
        max_length=30,
        required=False,
        label=ugettext_noop("Organization's Registration or Tax Identification Number"),
        help_text=ugettext_noop(
            "A registration or tax identification number is the unique number your"
            " government uses to identify your organization. Please note that you "
            "should only give information that you are allowed to share and that "
            "is available to the public. You should not give nonpublic or "
            "confidential information."
        )
    )

    def __init__(self, *args, **kwargs):
        super(OrganizationMetricModelForm, self).__init__(*args, **kwargs)
        self.fields['actual_data'].empty_label = None
        self.fields['actual_data'].required = False

    class Meta:
        model = OrganizationMetric

        fields = [
            'can_provide_info', 'actual_data', 'effective_date', 'total_clients', 'total_employees', 'local_currency',
            'total_revenue', 'total_donations', 'total_expenses', 'total_program_expenses',
        ]

        widgets = {
            'can_provide_info': forms.RadioSelect,
            'actual_data': RadioSelectNotNull,
            'effective_date': forms.TextInput,
            'total_clients': forms.NumberInput,
            'total_employees': forms.NumberInput,
            'local_currency': forms.HiddenInput,
            'total_revenue': forms.NumberInput,
            'total_donations': forms.NumberInput,
            'total_expenses': forms.NumberInput,
            'total_program_expenses': forms.NumberInput,
        }

        labels = {
            'actual_data': ugettext_noop('Is the information you will provide on this page estimated or actual?*'),
            'total_clients': ugettext_noop('Total Annual Clients or Direct Beneficiaries for Last Fiscal Year'),
            'total_employees': ugettext_noop('Total Employees at the End of Last Fiscal Year'),
            'local_currency': ugettext_noop('Local Currency Code*'),
            'total_revenue': ugettext_noop('Total Annual Revenue for Last Fiscal Year (Local Currency)'),
            'total_donations': ugettext_noop('Total Donations and Grants Received Last Fiscal Year (Local Currency)'),
            'total_expenses': ugettext_noop('Total Annual Expenses for Last Fiscal Year (Local Currency)'),
            'total_program_expenses': ugettext_noop('Total Annual Program Expenses for Last Fiscal Year '
                                                    '(Local Currency)'),
        }

        help_texts = {
            "actual_data": ugettext_noop("If you don't have access to information from official documents, please give "
                                         "your best guesses based on your knowledge of your organization. Please note "
                                         "that you should only give information that you are allowed to share and that "
                                         "is available to the public. You should not give nonpublic or confidential "
                                         "information."),
            "total_clients": ugettext_noop("A client or direct beneficiary is any person benefiting directly from your "
                                           "organization's activities through face-to-face contact with program staff, "
                                           "often in a one-on-one or small-group setting. Please do not include "
                                           "indirect beneficiaries or people your organization reaches on a lighter "
                                           "scale, such as through one-time events. If your organization does not "
                                           "serve people directly because, for example, you work with animals, the "
                                           "environment, or in arts and culture, please provide a reasonable estimate "
                                           "for the number of people or animals that benefit from your services."),
            "total_employees": ugettext_noop("An employee is a member of your staff who is paid for their work. A staff"
                                             " member working full-time counts as 1 employee; a staff member working "
                                             "half-time counts as 0.5 of an employee. Please include yourself in your "
                                             "organization's employee count. We asked a similar question on the last "
                                             "page, but here we are asking for the number of employees at the end of "
                                             "your last fiscal year instead of your current number."),
            "total_revenue": ugettext_noop("Revenue is the total amount of money your organization receives, regardless"
                                           "of the source of that funding. Sources of revenue may include fees for "
                                           "services and goods, government contracts, donations, grants, or investment "
                                           "income."),
            "total_donations": ugettext_noop("Donations and grants are two different sources of revenue. A donation is"
                                             " funding given to your organization with nothing or very little "
                                             "expected in return. An unrestricted cash gift from a private individual"
                                             " is a donation. A grant is funding given to your organization for a"
                                             " particular purpose with some obligations, such as reporting.  Revenue"
                                             " from government sources should also be included in this line."),
            "total_expenses": ugettext_noop("An expense is money your organization spends in order to deliver its "
                                            "programs, operate the business, and generate revenue. Expenses may "
                                            "include. wages and salaries, rent, insurance, travel, or supplies."),
            "total_program_expenses": ugettext_noop("A program expense is money your organization spends exclusively "
                                                    "in order to deliver its programs and should not include "
                                                    "administrative or fundraising expenses. These program expenses"
                                                    " should also be included in your total annual expenses for last "
                                                    "fiscal year above."),
        }

    def clean_actual_data(self):
        can_provide_info = int(self.data['can_provide_info']) if self.data.get('can_provide_info') else False
        info_accuracy = self.cleaned_data['actual_data']

        if can_provide_info and info_accuracy not in [True, False]:
            raise forms.ValidationError(ugettext_noop("Please select an option for Estimated or Actual Information"))

        return info_accuracy

    def clean_effective_date(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        last_fiscal_year_end_date = self.cleaned_data['effective_date']

        if can_provide_info and not last_fiscal_year_end_date:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("End date for Last Fiscal Year")))

        if last_fiscal_year_end_date and last_fiscal_year_end_date > datetime.now().date():
            raise forms.ValidationError(ugettext_noop("Please enter a valid End date for Last Fiscal Year"))

        return last_fiscal_year_end_date

    def clean_total_clients(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_clients = self.cleaned_data['total_clients']

        if can_provide_info and not total_clients:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Client")))

        return total_clients

    def clean_total_employees(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_employees = self.cleaned_data['total_employees']

        if can_provide_info and not total_employees:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Employees")))

        return total_employees

    def clean_local_currency(self):
        can_provide_info = int(self.data['can_provide_info']) if self.data.get('can_provide_info') else False
        all_currency_codes = Currency.objects.values_list('alphabetic_code', flat=True)
        currency_input = self.cleaned_data['local_currency']

        if can_provide_info and currency_input not in all_currency_codes:
            raise forms.ValidationError(ugettext_noop('Please select Currency Code.'))

        return currency_input

    def clean_total_revenue(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_revenue = self.cleaned_data['total_revenue']

        if can_provide_info and not total_revenue:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Revenue")))

        return total_revenue

    def clean_total_donations(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_donations = self.cleaned_data['total_donations']

        if can_provide_info and not total_donations:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Donations")))

        return total_donations

    def clean_total_expenses(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_expenses = self.cleaned_data['total_expenses']

        if can_provide_info and not total_expenses:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Expenses")))

        return total_expenses

    def clean_total_program_expenses(self):
        can_provide_info = int(self.data.get('can_provide_info')) if self.data.get('can_provide_info') else False
        total_program_expenses = self.cleaned_data['total_program_expenses']

        if can_provide_info and not total_program_expenses:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Program Expense")))

        return total_program_expenses

    def save(self, request):
        user_extended_profile = request.user.extended_profile
        can_provide_info = int(self.data['can_provide_info'])

        if can_provide_info:
            org_detail = super(OrganizationMetricModelForm, self).save(commit=False)
            org_detail.user = request.user
            org_detail.org = user_extended_profile.organization
            org_detail.local_currency = Currency.objects.filter(
                alphabetic_code=self.cleaned_data['local_currency']).first().alphabetic_code

            org_detail.save()

        if self.data['registration_number']:
            user_extended_profile.organization.registration_number = self.data['registration_number']
            user_extended_profile.organization.save()

        user_extended_profile.is_organization_metrics_submitted = True
        user_extended_profile.save()


class OrganizationMetricModelUpdateForm(OrganizationMetricModelForm):
    effective_date = forms.DateField(input_formats=['%m/%d/%Y'],
                                     required=False,
                                     help_text=ugettext_noop("The fiscal year is the period that an organization uses "
                                                             "for accounting  purposes and preparing financial "
                                                             "statements. A fiscal year may or may not be the same"
                                                             " as a calendar year. If the information you are "
                                                             "giving below is for the last 12 months, please enter "
                                                             "today's date."),
                                     label=ugettext_noop('End Date of Last Fiscal Year'),
                                     label_suffix='*')

    registration_number = forms.CharField(max_length=30,
                                          required=False,
                                          label=ugettext_noop(
                                              "Organization's Registration or Tax Identification Number"),
                                          help_text=ugettext_noop(
                                              "A registration or tax identification number is the unique number your"
                                              " government uses to identify your organization. Please note that you "
                                              "should only give information that you are allowed to share and that "
                                              "is available to the public. You should not give nonpublic or "
                                              "confidential information."))

    def __init__(self, *args, **kwargs):
        super(OrganizationMetricModelForm, self).__init__(*args, **kwargs)
        self.fields['actual_data'].empty_label = None
        self.fields['actual_data'].required = False
        self.fields['can_provide_info'].required = False

    class Meta:
        model = OrganizationMetric

        fields = [
            'actual_data', 'effective_date', 'total_clients', 'total_employees', 'local_currency',
            'total_revenue', 'total_donations', 'total_expenses', 'total_program_expenses'
        ]

        widgets = {
            'actual_data': RadioSelectNotNull,
            'effective_date': forms.TextInput,
            'total_clients': forms.NumberInput,
            'total_employees': forms.NumberInput,
            'local_currency': forms.HiddenInput,
            'total_revenue': forms.NumberInput,
            'total_donations': forms.NumberInput,
            'total_expenses': forms.NumberInput,
            'total_program_expenses': forms.NumberInput,
        }

        labels = {
            'actual_data': ugettext_noop('Is the information you will provide on this page estimated or actual?'),
            'total_clients': ugettext_noop('Total Annual Clients or Direct Beneficiaries for Last Fiscal Year'),
            'total_employees': ugettext_noop('Total Employees at the End of Last Fiscal Year'),
            'local_currency': ugettext_noop('Local Currency Code*'),
            'total_revenue': ugettext_noop('Total Annual Revenue for Last Fiscal Year (Local Currency)'),
            'total_donations': ugettext_noop('Total Donations and Grants Received Last Fiscal Year (Local Currency)'),
            'total_expenses': ugettext_noop('Total Annual Expenses for Last Fiscal Year (Local Currency)'),
            'total_program_expenses': ugettext_noop('Total Annual Program Expenses for Last Fiscal Year '
                                                    '(Local Currency)'),
        }

        help_texts = {
            "actual_data": ugettext_noop("If you don't have access to information from official documents, please give "
                                         "your best guesses based on your knowledge of your organization. Please note "
                                         "that you should only give information that you are allowed to share and that "
                                         "is available to the public. You should not give nonpublic or confidential "
                                         "information."),
            "total_clients": ugettext_noop("A client or direct beneficiary is any person benefiting directly from your "
                                           "organization's activities through face-to-face contact with program staff, "
                                           "often in a one-on-one or small-group setting. Please do not include "
                                           "indirect beneficiaries or people your organization reaches on a lighter "
                                           "scale, such as through one-time events. If your organization does not "
                                           "serve people directly because, for example, you work with animals, the "
                                           "environment, or in arts and culture, please provide a reasonable estimate "
                                           "for the number of people or animals that benefit from your services."),
            "total_employees": ugettext_noop("An employee is a member of your staff who is paid for their work. A staff"
                                             " member working full-time counts as 1 employee; a staff member working "
                                             "half-time counts as 0.5 of an employee. Please include yourself in your "
                                             "organization's employee count. We asked a similar question on the last "
                                             "page, but here we are asking for the number of employees at the end of "
                                             "your last fiscal year instead of your current number."),
            "total_revenue": ugettext_noop("Revenue is the total amount of money your organization receives, regardless"
                                           "of the source of that funding. Sources of revenue may include fees for "
                                           "services and goods, government contracts, donations, grants, or investment "
                                           "income."),
            "total_donations": ugettext_noop("Donations and grants are two different sources of revenue. A donation is"
                                             " funding given to your organization with nothing or very little "
                                             "expected in return. An unrestricted cash gift from a private individual"
                                             " is a donation. A grant is funding given to your organization for a"
                                             " particular purpose with some obligations, such as reporting.  Revenue"
                                             " from government sources should also be included in this line."),
            "total_expenses": ugettext_noop("An expense is money your organization spends in order to deliver its "
                                            "programs, operate the business, and generate revenue. Expenses may "
                                            "include. wages and salaries, rent, insurance, travel, or supplies."),
            "total_program_expenses": ugettext_noop("A program expense is money your organization spends exclusively "
                                                    "in order to deliver its programs and should not include "
                                                    "administrative or fundraising expenses. These program expenses"
                                                    " should also be included in your total annual expenses for last "
                                                    "fiscal year above."),
        }

    def clean_actual_data(self):
        info_accuracy = self.cleaned_data['actual_data']

        if info_accuracy not in [True, False]:
            raise forms.ValidationError(ugettext_noop("Please select an option for Estimated or Actual Information"))

        return info_accuracy

    def clean_effective_date(self):
        last_fiscal_year_end_date = self.cleaned_data['effective_date']

        if not last_fiscal_year_end_date:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("End date for Last Fiscal Year")))

        if last_fiscal_year_end_date and last_fiscal_year_end_date > datetime.now().date():
            raise forms.ValidationError(ugettext_noop("Please enter a valid End date for Last Fiscal Year"))

        return last_fiscal_year_end_date

    def clean_total_clients(self):
        total_clients = self.cleaned_data['total_clients']

        if not total_clients:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Client")))

        return total_clients

    def clean_total_employees(self):
        total_employees = self.cleaned_data['total_employees']

        if not total_employees:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Employees")))

        return total_employees

    def clean_local_currency(self):
        all_currency_codes = Currency.objects.values_list('alphabetic_code', flat=True)
        currency_input = self.cleaned_data['local_currency']

        if currency_input not in all_currency_codes:
            raise forms.ValidationError(ugettext_noop('Please select currency code.'))

        return currency_input

    def clean_total_revenue(self):
        total_revenue = self.cleaned_data['total_revenue']

        if not total_revenue:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Revenue")))

        return total_revenue

    def clean_total_donations(self):
        total_donations = self.cleaned_data['total_donations']

        if not total_donations:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Donations")))

        return total_donations

    def clean_total_expenses(self):
        total_expenses = self.cleaned_data['total_expenses']

        if not total_expenses:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Expenses")))

        return total_expenses

    def clean_total_program_expenses(self):
        total_program_expenses = self.cleaned_data['total_program_expenses']

        if not total_program_expenses:
            raise forms.ValidationError(ugettext_noop(EMPTY_FIELD_ERROR.format("Total Program Expense")))

        return total_program_expenses

    def save(self, request):
        user_extended_profile = request.user.extended_profile
        self.instance.pk = None
        org_detail = super(OrganizationMetricModelForm, self).save(commit=False)
        org_detail.user = request.user
        org_detail.org = user_extended_profile.organization
        org_detail.local_currency = Currency.objects.filter(
            alphabetic_code=self.cleaned_data['local_currency']).first().alphabetic_code

        org_detail.save()

        if self.data['registration_number']:
            user_extended_profile.organization.registration_number = self.data['registration_number']
            user_extended_profile.organization.save()

        user_extended_profile.is_organization_metrics_submitted = True
        user_extended_profile.save()
