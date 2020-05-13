import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_api.accounts.api import check_account_exists

from student import forms as student_forms
from student.models import CourseEnrollmentAllowed, email_exists_or_retired
from util.password_policy_validators import validate_password

from lms.djangoapps.onboarding.helpers import COUNTRIES


def validate_name(name):
    """
    Verifies a Full_Name is valid, raises a ValidationError otherwise.
    Args:
        name (unicode): The name to validate.
    """
    if student_forms.contains_html(name):
        raise forms.ValidationError('Full Name cannot contain the following characters: < >')

    name_split = name.strip().split(' ', 1)
    if len(name_split) < 2:
        raise forms.ValidationError('Full Name must include first name and last name')


class PartnerResetPasswordForm(student_forms.PasswordResetFormNoActive):
    """
    A form to validate reset password data for partner users. This is currently only
    being used to override an error message as per the requirements.
    """
    def clean_email(self):
        self.error_messages['unknown'] = _('We don\'t recognize the email: {}').format(self.cleaned_data['email'])
        return super(PartnerResetPasswordForm, self).clean_email()


class UsernameField(student_forms.UsernameField):
    """
    Inheriting UsernameField from student app. Parent class is not validating username already exists
    """

    def clean(self, value):
        clean_username = super(UsernameField, self).clean(value)

        # check if user name is not already taken
        conflicts = check_account_exists(username=clean_username)
        if conflicts and 'username' in conflicts:
            raise forms.ValidationError(
                'The username you entered is already being used. Please enter another username.')

        return clean_username


class PartnerAccountCreationForm(forms.Form):
    """
    A form to validate account creation data for Give2Asia. It is currently only used for
    validation, not rendering.
    """

    _NAME_MIN_LENGTH = 3
    _EMAIL_INVALID_MSG = 'A properly formatted e-mail is required'
    _NAME_TOO_SHORT_MSG = 'Your legal name must be a minimum of three characters long'

    def __init__(self, data=None, tos_required=True):
        super(PartnerAccountCreationForm, self).__init__(data)
        if tos_required:
            self.fields['terms_of_service'] = student_forms.TrueField(
                error_messages={'required': 'You must accept the terms of service.'}
            )

    def clean_password(self):
        """ Enforce password policies (if applicable) """
        password = self.cleaned_data['password']
        # Creating a temporary user object to test password against username
        # This user should NOT be saved
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        temp_user = User(username=username, email=email) if username else None
        validate_password(password, temp_user)
        return password

    def clean_email(self):
        """ Enforce email restrictions (if applicable) """
        email = self.cleaned_data['email']
        if settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED is not None:
            # This Open edX instance has restrictions on what email addresses are allowed.
            allowed_patterns = settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED
            # We append a '$' to the regexs to prevent the common mistake of using a
            # pattern like '.*@edx\\.org' which would match 'bob@edx.org.badguy.com'
            if not any(re.match(pattern + '$', email) for pattern in allowed_patterns):
                # This email is not on the whitelist of allowed emails. Check if
                # they may have been manually invited by an instructor and if not,
                # reject the registration.
                if not CourseEnrollmentAllowed.objects.filter(email=email).exists():
                    raise ValidationError('Unauthorized email address.')
        if email_exists_or_retired(email):
            raise ValidationError(
                _('Looks like that email address is taken. Try a different one.')
            )
        return email

    def clean_name(self):
        """ Clean name by splitting it into first name and last name """
        return self.cleaned_data['name'].split(' ', 1)

    def clean_registration_data(self, registration_data):
        """ Once form is validated, call this function to get clean registration data """
        registration_data.update(self.cleaned_data)

    def clean_country(self):
        country_code = self.cleaned_data['country']
        cleaned_country = next((code for code in COUNTRIES.keys() if code == country_code), None)
        if cleaned_country:
            return cleaned_country
        raise ValidationError(_('Please select country.'))

    username = UsernameField()
    password = forms.CharField()
    email = forms.EmailField(
        max_length=accounts_settings.EMAIL_MAX_LENGTH,
        min_length=accounts_settings.EMAIL_MIN_LENGTH,
        error_messages={
            'required': _EMAIL_INVALID_MSG,
            'invalid': _EMAIL_INVALID_MSG,
            'max_length': 'Email cannot be more than %(limit_value)s characters long',
        }
    )
    name = forms.CharField(
        min_length=_NAME_MIN_LENGTH,
        error_messages={
            'required': _NAME_TOO_SHORT_MSG,
            'min_length': _NAME_TOO_SHORT_MSG,
        },
        validators=[validate_name]
    )
    organization_name = forms.CharField(
        max_length=255,
        error_messages={
            'required': _('Organization name is required'),
        },
    )

    country = forms.CharField(
        error_messages={
            'required': _('Country name is required'),
        },
    )

