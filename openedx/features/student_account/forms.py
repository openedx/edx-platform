"""
Utility functions for validating forms
"""
import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.onboarding.models import Organization, OrgSector, TotalEmployee
from openedx.core.djangoapps.user_api import accounts as accounts_settings
from student.forms import contains_html, UsernameField, validate_name
from student.models import CourseEnrollmentAllowed, email_exists_or_retired
from util.password_policy_validators import validate_password


class AccountCreationFormCustom(forms.Form):
    """
    A form for account creation data. It is currently only used for
    validation, not rendering.
    """

    _EMAIL_INVALID_MSG = _("A properly formatted e-mail is required")
    _NAME_TOO_SHORT_MSG = _("Your full name must be a minimum of two characters long")
    _OPT_IN_REQUIRED_MSG = _("Email opt in is a required field, and can only be set to true or false")

    # TODO: Resolve repetition

    username = UsernameField()

    email = forms.EmailField(
        max_length=accounts_settings.EMAIL_MAX_LENGTH,
        min_length=accounts_settings.EMAIL_MIN_LENGTH,
        error_messages={
            "required": _EMAIL_INVALID_MSG,
            "invalid": _EMAIL_INVALID_MSG,
            "max_length": _("Email cannot be more than %(limit_value)s characters long"),
        }
    )

    password = forms.CharField()

    name = forms.CharField(
        min_length=accounts_settings.NAME_MIN_LENGTH,
        error_messages={
            "required": _NAME_TOO_SHORT_MSG,
            "min_length": _NAME_TOO_SHORT_MSG,
        },
        validators=[validate_name]
    )

    org_size = forms.CharField(
        required=False
    )

    org_type = forms.CharField(
        required=False
    )

    org_name = forms.CharField(
        max_length=255,
        required=False
    )

    opt_in = forms.CharField(
        error_messages={
            "required": _OPT_IN_REQUIRED_MSG,
        }
    )

    def __init__(self, data=None, extended_profile_fields=None, do_third_party_auth=True):
        super(AccountCreationFormCustom, self).__init__(data)
        self.extended_profile_fields = extended_profile_fields or {}
        self.do_third_party_auth = do_third_party_auth

    def clean_password(self):
        """Enforce password policies (if applicable)"""
        password = self.cleaned_data["password"]
        if not self.do_third_party_auth:
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
                    raise ValidationError(_("Unauthorized email address."))
        if email_exists_or_retired(email):
            raise ValidationError(
                _(
                    "It looks like {email} belongs to an existing account. Try again with a different email address."
                ).format(email=email)
            )
        return email

    def clean_opt_in(self):
        """
        Verifies a opt_in is valid only either "yes", or "no",
        raises a ValidationError otherwise.
        Args:
            opt_in (unicode): The opt_in value to validate.
        """
        cleaned_opt_in = self.cleaned_data.get("opt_in")
        if cleaned_opt_in not in ["yes", "no"]:
            raise ValidationError({'opt_in': [_('Invalid email opt in option provided'), ]})
        return cleaned_opt_in

    def clean(self):
        """ Enforce organization related field conditions"""
        cleaned_org_name = self.cleaned_data.get("org_name")
        cleaned_org_size = self.cleaned_data.get("org_size")
        cleaned_org_type = self.cleaned_data.get("org_type")

        valid_org_type = OrgSector.objects.filter(code=cleaned_org_type).exists()
        valid_org_size = TotalEmployee.objects.filter(code=cleaned_org_size).exists()

        if cleaned_org_type and not valid_org_type:
            raise ValidationError({'org_type': [_('Invalid organization type option provided'), ]})

        if cleaned_org_size and not valid_org_size:
            raise ValidationError({'org_size': [_('Invalid organization size option provided'), ]})

        # User is affiliated with some organization
        if cleaned_org_name:
            # Check if organization already exists and does have a size populated
            existing_org = Organization.objects.filter(label=cleaned_org_name).first()

            if existing_org:
                existing_org_size = existing_org.total_employees
                existing_org_type = existing_org.org_type
                if not existing_org_size and not cleaned_org_size:
                    raise ValidationError({'org_size': [_("Organization size not provided."), ]})
                elif existing_org_size and cleaned_org_size:
                    raise ValidationError({'org_size': [_("Organization size provided for existing organization"), ]})

                if not existing_org_type and not cleaned_org_type:
                    raise ValidationError({'org_type': [_("Organization type not provided."), ]})
                elif existing_org_type and cleaned_org_type:
                    raise ValidationError({'org_type': [_("Organization type provided for existing organization"), ]})

            else:
                if not cleaned_org_size:
                    raise ValidationError({'org_size': [_("Organization size not provided for new organization"), ]})
                if not cleaned_org_type:
                    raise ValidationError({'org_type': [_("Organization type not provided for new organization"), ]})

        return self.cleaned_data

    @property
    def cleaned_extended_profile(self):
        """
        Return a dictionary containing the extended_profile_fields and values
        """
        return {
            key: value
            for key, value in self.cleaned_data.items()
            if key in self.extended_profile_fields and value is not None
        }

