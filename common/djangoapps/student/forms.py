"""
Utility functions for validating forms
"""
from importlib import import_module
import re

from django import forms
from django.forms import widgets
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.tokens import default_token_generator

from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from django.template import loader

from django.conf import settings
from student.models import CourseEnrollmentAllowed
from util.password_policy_validators import validate_password_strength
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class PasswordResetFormNoActive(PasswordResetForm):
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }

    def clean_email(self):
        """
        This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except removing the requirement of active users
        Validates that a user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password.startswith(UNUSABLE_PASSWORD_PREFIX))
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(
            self,
            domain_override=None,
            subject_template_name='registration/password_reset_subject.txt',
            email_template_name='registration/password_reset_email.html',
            use_https=False,
            token_generator=default_token_generator,
            from_email=configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
            request=None
    ):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        # This import is here because we are copying and modifying the .save from Django 1.4.5's
        # django.contrib.auth.forms.PasswordResetForm directly, which has this import in this place.
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                site_name = configuration_helpers.get_value(
                    'SITE_NAME',
                    settings.SITE_NAME
                )
            else:
                site_name = domain_override
            context = {
                'email': user.email,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
            }
            subject = loader.render_to_string(subject_template_name, context)
            # Email subject *must not* contain newlines
            subject = subject.replace('\n', '')
            email = loader.render_to_string(email_template_name, context)
            send_mail(subject, email, from_email, [user.email])


class TrueCheckbox(widgets.CheckboxInput):
    """
    A checkbox widget that only accepts "true" (case-insensitive) as true.
    """
    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        return value.lower() == 'true'


class TrueField(forms.BooleanField):
    """
    A boolean field that only accepts "true" (case-insensitive) as true
    """
    widget = TrueCheckbox


_USERNAME_TOO_SHORT_MSG = _("Username must be minimum of two characters long")
_EMAIL_INVALID_MSG = _("A properly formatted e-mail is required")
_PASSWORD_INVALID_MSG = _("A valid password is required")
_NAME_TOO_SHORT_MSG = _("Your legal name must be a minimum of two characters long")


class AccountCreationForm(forms.Form):
    """
    A form to for account creation data. It is currently only used for
    validation, not rendering.
    """
    # TODO: Resolve repetition
    username = forms.SlugField(
        min_length=2,
        max_length=30,
        error_messages={
            "required": _USERNAME_TOO_SHORT_MSG,
            "invalid": _("Usernames must contain only letters, numbers, underscores (_), and hyphens (-)."),
            "min_length": _USERNAME_TOO_SHORT_MSG,
            "max_length": _("Username cannot be more than %(limit_value)s characters long"),
        }
    )
    email = forms.EmailField(
        max_length=254,  # Limit per RFCs is 254
        error_messages={
            "required": _EMAIL_INVALID_MSG,
            "invalid": _EMAIL_INVALID_MSG,
            "max_length": _("Email cannot be more than %(limit_value)s characters long"),
        }
    )
    password = forms.CharField(
        min_length=2,
        error_messages={
            "required": _PASSWORD_INVALID_MSG,
            "min_length": _PASSWORD_INVALID_MSG,
        }
    )
    name = forms.CharField(
        min_length=2,
        error_messages={
            "required": _NAME_TOO_SHORT_MSG,
            "min_length": _NAME_TOO_SHORT_MSG,
        }
    )

    def __init__(
            self,
            data=None,
            extra_fields=None,
            extended_profile_fields=None,
            enforce_username_neq_password=False,
            enforce_password_policy=False,
            tos_required=True
    ):
        super(AccountCreationForm, self).__init__(data)

        extra_fields = extra_fields or {}
        self.extended_profile_fields = extended_profile_fields or {}
        self.enforce_username_neq_password = enforce_username_neq_password
        self.enforce_password_policy = enforce_password_policy
        if tos_required:
            self.fields["terms_of_service"] = TrueField(
                error_messages={"required": _("You must accept the terms of service.")}
            )

        # TODO: These messages don't say anything about minimum length
        error_message_dict = {
            "level_of_education": _("A level of education is required"),
            "gender": _("Your gender is required"),
            "year_of_birth": _("Your year of birth is required"),
            "mailing_address": _("Your mailing address is required"),
            "goals": _("A description of your goals is required"),
            "city": _("A city is required"),
            "country": _("A country is required")
        }
        for field_name, field_value in extra_fields.items():
            if field_name not in self.fields:
                if field_name == "honor_code":
                    if field_value == "required":
                        self.fields[field_name] = TrueField(
                            error_messages={
                                "required": _("To enroll, you must follow the honor code.")
                            }
                        )
                elif field_name == 'data_sharing_consent':
                    if field_value == "required":
                        self.fields[field_name] = TrueField(
                            error_messages={
                                "required": _("Your SSO identity provider requires you to consent to course data sharing.")
                            }
                        )
                    else:
                        self.fields[field_name] = forms.BooleanField(
                            required=False
                        )
                else:
                    required = field_value == "required"
                    min_length = 1 if field_name in ("gender", "level_of_education") else 2
                    error_message = error_message_dict.get(
                        field_name,
                        _("You are missing one or more required fields")
                    )
                    self.fields[field_name] = forms.CharField(
                        required=required,
                        min_length=min_length,
                        error_messages={
                            "required": error_message,
                            "min_length": error_message,
                        }
                    )

        for field in self.extended_profile_fields:
            if field not in self.fields:
                self.fields[field] = forms.CharField(required=False)

    def clean_password(self):
        """Enforce password policies (if applicable)"""
        password = self.cleaned_data["password"]
        if (
                self.enforce_username_neq_password and
                "username" in self.cleaned_data and
                self.cleaned_data["username"] == password
        ):
            raise ValidationError(_("Username and password fields cannot match"))
        if self.enforce_password_policy:
            try:
                validate_password_strength(password)
            except ValidationError, err:
                raise ValidationError(_("Password: ") + "; ".join(err.messages))
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
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _(
                    "It looks like {email} belongs to an existing account. Try again with a different email address."
                ).format(email=email)
            )
        return email

    def clean_year_of_birth(self):
        """
        Parse year_of_birth to an integer, but just use None instead of raising
        an error if it is malformed
        """
        try:
            year_str = self.cleaned_data["year_of_birth"]
            return int(year_str) if year_str is not None else None
        except ValueError:
            return None

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


def get_registration_extension_form(*args, **kwargs):
    """
    Convenience function for getting the custom form set in settings.REGISTRATION_EXTENSION_FORM.

    An example form app for this can be found at http://github.com/open-craft/custom-form-app
    """
    if not settings.FEATURES.get("ENABLE_COMBINED_LOGIN_REGISTRATION"):
        return None
    if not getattr(settings, 'REGISTRATION_EXTENSION_FORM', None):
        return None
    module, klass = settings.REGISTRATION_EXTENSION_FORM.rsplit('.', 1)
    module = import_module(module)
    return getattr(module, klass)(*args, **kwargs)
