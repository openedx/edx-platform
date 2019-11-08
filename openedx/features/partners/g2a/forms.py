import re
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from lms.djangoapps.onboarding.models import Organization
from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_api.accounts.api import check_account_exists
from student import forms as student_forms
from student.models import CourseEnrollmentAllowed, email_exists_or_retired
from util.password_policy_validators import validate_password


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
                "The username you entered is already being used. Please enter another username.")

        return clean_username


class Give2AsiaAccountCreationForm(forms.Form):
    """
    A form to validate account creation data for Give2Asia. It is currently only used for
    validation, not rendering.
    """

    _NAME_MIN_LENGTH = 3
    _EMAIL_INVALID_MSG = "A properly formatted e-mail is required"
    _NAME_TOO_SHORT_MSG = "Your legal name must be a minimum of three characters long"

    username = UsernameField()

    email = forms.EmailField(
        max_length=accounts_settings.EMAIL_MAX_LENGTH,
        min_length=accounts_settings.EMAIL_MIN_LENGTH,
        error_messages={
            "required": _EMAIL_INVALID_MSG,
            "invalid": _EMAIL_INVALID_MSG,
            "max_length": "Email cannot be more than %(limit_value)s characters long",
        }
    )

    password = forms.CharField()

    def validate_name(name):
        """
        Verifies a Full_Name is valid, raises a ValidationError otherwise.
        Args:
            name (unicode): The name to validate.
        """
        if student_forms.contains_html(name):
            raise forms.ValidationError('Full Name cannot contain the following characters: < >')

        name_split = name.strip().split(" ", 1)
        if len(name_split) < 2:
            raise forms.ValidationError("Full Name must include first name and last name")

    name = forms.CharField(
        min_length=_NAME_MIN_LENGTH,
        error_messages={
            "required": _NAME_TOO_SHORT_MSG,
            "min_length": _NAME_TOO_SHORT_MSG,
        },
        validators=[validate_name]
    )

    def validate_organization_name(organization_name):
        """ Check if organization associated to partner exists"""
        organization = Organization.objects.filter(label__iexact=organization_name).first()
        if organization is None:
            raise forms.ValidationError("Organization associated to this partner is not found")

    organization_name = forms.CharField(
        error_messages={
            "required": "Valid organization name associated to this partner is required",
        },
        validators=[validate_organization_name]
    )

    def __init__(
        self,
        data=None,
        tos_required=True
    ):
        super(Give2AsiaAccountCreationForm, self).__init__(data)

        if tos_required:
            self.fields["terms_of_service"] = student_forms.TrueField(
                error_messages={"required": "You must accept the terms of service."}
            )

    def clean_password(self):
        """Enforce password policies (if applicable)"""
        password = self.cleaned_data["password"]
        # Creating a temporary user object to test password against username
        # This user should NOT be saved
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        temp_user = User(username=username, email=email) if username else None
        validate_password(password, temp_user)
        return password

    def clean_email(self):
        """ Enforce email restrictions (if applicable) """
        email = self.cleaned_data["email"]
        if settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED is not None:
            # This Open edX instance has restrictions on what email addresses are allowed.
            allowed_patterns = settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED
            # We append a '$' to the regexs to prevent the common mistake of using a
            # pattern like '.*@edx\\.org' which would match 'bob@edx.org.badguy.com'
            if not any(re.match(pattern + "$", email) for pattern in allowed_patterns):
                # This email is not on the whitelist of allowed emails. Check if
                # they may have been manually invited by an instructor and if not,
                # reject the registration.
                if not CourseEnrollmentAllowed.objects.filter(email=email).exists():
                    raise ValidationError("Unauthorized email address.")
        if email_exists_or_retired(email):
            raise ValidationError(
                "It looks like {email} belongs to an existing account. Try again with a different email address."
                    .format(email=email)
            )
        return email
