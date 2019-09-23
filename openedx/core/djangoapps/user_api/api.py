import copy
import crum

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import ugettext as _
from django_countries import countries

import accounts
import third_party_auth
from edxmako.shortcuts import marketing_link
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from student.forms import get_registration_extension_form
from student.models import UserProfile
from util.password_policy_validators import (
    password_validators_instruction_texts, password_validators_restrictions, DEFAULT_MAX_PASSWORD_LENGTH,
)


def get_password_reset_form():
    """Return a description of the password reset form.

    This decouples clients from the API definition:
    if the API decides to modify the form, clients won't need
    to be updated.

    See `user_api.helpers.FormDescription` for examples
    of the JSON-encoded form description.

    Returns:
        HttpResponse

    """
    form_desc = FormDescription("post", reverse("password_change_request"))

    # Translators: This label appears above a field on the password reset
    # form meant to hold the user's email address.
    email_label = _(u"Email")

    # Translators: This example email address is used as a placeholder in
    # a field on the password reset form meant to hold the user's email address.
    email_placeholder = _(u"username@domain.com")

    # Translators: These instructions appear on the password reset form,
    # immediately below a field meant to hold the user's email address.
    email_instructions = _(u"The email address you used to register with {platform_name}").format(
        platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
    )

    form_desc.add_field(
        "email",
        field_type="email",
        label=email_label,
        placeholder=email_placeholder,
        instructions=email_instructions,
        restrictions={
            "min_length": accounts.EMAIL_MIN_LENGTH,
            "max_length": accounts.EMAIL_MAX_LENGTH,
        }
    )

    return form_desc


def get_account_recovery_form():
    """
    Return a description of the password reset, using secondary email, form.

    This decouples clients from the API definition:
    if the API decides to modify the form, clients won't need
    to be updated.

    See `user_api.helpers.FormDescription` for examples
    of the JSON-encoded form description.

    Returns:
        HttpResponse

    """
    form_desc = FormDescription("post", reverse("account_recovery"))

    # Translators: This label appears above a field on the password reset
    # form meant to hold the user's email address.
    email_label = _(u"Secondary email")

    # Translators: This example email address is used as a placeholder in
    # a field on the password reset form meant to hold the user's email address.
    email_placeholder = _(u"username@domain.com")

    # Translators: These instructions appear on the password reset form,
    # immediately below a field meant to hold the user's email address.
    email_instructions = _(
        u"Secondary email address you registered with {platform_name} using account settings page"
    ).format(
        platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
    )

    form_desc.add_field(
        "email",
        field_type="email",
        label=email_label,
        placeholder=email_placeholder,
        instructions=email_instructions,
        restrictions={
            "min_length": accounts.EMAIL_MIN_LENGTH,
            "max_length": accounts.EMAIL_MAX_LENGTH,
        }
    )

    return form_desc


def get_login_session_form(request):
    """Return a description of the login form.

    This decouples clients from the API definition:
    if the API decides to modify the form, clients won't need
    to be updated.

    See `user_api.helpers.FormDescription` for examples
    of the JSON-encoded form description.

    Returns:
        HttpResponse

    """
    form_desc = FormDescription("post", reverse("user_api_login_session"))
    _apply_third_party_auth_overrides(request, form_desc)

    # Translators: This label appears above a field on the login form
    # meant to hold the user's email address.
    email_label = _(u"Email")

    # Translators: This example email address is used as a placeholder in
    # a field on the login form meant to hold the user's email address.
    email_placeholder = _(u"username@domain.com")

    # Translators: These instructions appear on the login form, immediately
    # below a field meant to hold the user's email address.
    email_instructions = _("The email address you used to register with {platform_name}").format(
        platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
    )

    form_desc.add_field(
        "email",
        field_type="email",
        label=email_label,
        placeholder=email_placeholder,
        instructions=email_instructions,
        restrictions={
            "min_length": accounts.EMAIL_MIN_LENGTH,
            "max_length": accounts.EMAIL_MAX_LENGTH,
        }
    )

    # Translators: This label appears above a field on the login form
    # meant to hold the user's password.
    password_label = _(u"Password")

    form_desc.add_field(
        "password",
        label=password_label,
        field_type="password",
        restrictions={'max_length': DEFAULT_MAX_PASSWORD_LENGTH}
    )

    form_desc.add_field(
        "remember",
        field_type="checkbox",
        label=_("Remember me"),
        default=False,
        required=False,
    )

    return form_desc


def _apply_third_party_auth_overrides(request, form_desc):
    """Modify the login form if the user has authenticated with a third-party provider.
    If a user has successfully authenticated with a third-party provider,
    and an email is associated with it then we fill in the email field with readonly property.
    Arguments:
        request (HttpRequest): The request for the registration form, used
            to determine if the user has successfully authenticated
            with a third-party provider.
        form_desc (FormDescription): The registration form description
    """
    if third_party_auth.is_enabled():
        running_pipeline = third_party_auth.pipeline.get(request)
        if running_pipeline:
            current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)
            if current_provider and enterprise_customer_for_request(request):
                pipeline_kwargs = running_pipeline.get('kwargs')

                # Details about the user sent back from the provider.
                details = pipeline_kwargs.get('details')
                email = details.get('email', '')

                # override the email field.
                form_desc.override_field_properties(
                    "email",
                    default=email,
                    restrictions={"readonly": "readonly"} if email else {
                        "min_length": accounts.EMAIL_MIN_LENGTH,
                        "max_length": accounts.EMAIL_MAX_LENGTH,
                    }
                )


class RegistrationFormFactory(object):
    """HTTP end-points for creating a new user. """

    DEFAULT_FIELDS = ["email", "name", "username", "password"]

    EXTRA_FIELDS = [
        "confirm_email",
        "first_name",
        "last_name",
        "city",
        "state",
        "country",
        "gender",
        "year_of_birth",
        "level_of_education",
        "company",
        "job_title",
        "title",
        "mailing_address",
        "goals",
        "honor_code",
        "terms_of_service",
        "profession",
        "specialty",
    ]

    def _is_field_visible(self, field_name):
        """Check whether a field is visible based on Django settings. """
        return self._extra_fields_setting.get(field_name) in ["required", "optional"]

    def _is_field_required(self, field_name):
        """Check whether a field is required based on Django settings. """
        return self._extra_fields_setting.get(field_name) == "required"

    def __init__(self):

        # Backwards compatibility: Honor code is required by default, unless
        # explicitly set to "optional" in Django settings.
        self._extra_fields_setting = copy.deepcopy(configuration_helpers.get_value('REGISTRATION_EXTRA_FIELDS'))
        if not self._extra_fields_setting:
            self._extra_fields_setting = copy.deepcopy(settings.REGISTRATION_EXTRA_FIELDS)
        self._extra_fields_setting["honor_code"] = self._extra_fields_setting.get("honor_code", "required")

        # Check that the setting is configured correctly
        for field_name in self.EXTRA_FIELDS:
            if self._extra_fields_setting.get(field_name, "hidden") not in ["required", "optional", "hidden"]:
                msg = u"Setting REGISTRATION_EXTRA_FIELDS values must be either required, optional, or hidden."
                raise ImproperlyConfigured(msg)

        # Map field names to the instance method used to add the field to the form
        self.field_handlers = {}
        valid_fields = self.DEFAULT_FIELDS + self.EXTRA_FIELDS
        for field_name in valid_fields:
            handler = getattr(self, "_add_{field_name}_field".format(field_name=field_name))
            self.field_handlers[field_name] = handler

        field_order = configuration_helpers.get_value('REGISTRATION_FIELD_ORDER')
        if not field_order:
            field_order = settings.REGISTRATION_FIELD_ORDER or valid_fields

        # Check that all of the valid_fields are in the field order and vice versa, if not set to the default order
        if set(valid_fields) != set(field_order):
            field_order = valid_fields

        self.field_order = field_order

    def get_registration_form(self, request):
        """Return a description of the registration form.
        This decouples clients from the API definition:
        if the API decides to modify the form, clients won't need
        to be updated.
        This is especially important for the registration form,
        since different edx-platform installations might
        collect different demographic information.
        See `user_api.helpers.FormDescription` for examples
        of the JSON-encoded form description.
        Arguments:
            request (HttpRequest)
        Returns:
            HttpResponse
        """
        form_desc = FormDescription("post", reverse("user_api_registration"))
        self._apply_third_party_auth_overrides(request, form_desc)

        # Custom form fields can be added via the form set in settings.REGISTRATION_EXTENSION_FORM
        custom_form = get_registration_extension_form()

        if custom_form:
            # Default fields are always required
            for field_name in self.DEFAULT_FIELDS:
                self.field_handlers[field_name](form_desc, required=True)

            for field_name, field in custom_form.fields.items():
                restrictions = {}
                if getattr(field, 'max_length', None):
                    restrictions['max_length'] = field.max_length
                if getattr(field, 'min_length', None):
                    restrictions['min_length'] = field.min_length
                field_options = getattr(
                    getattr(custom_form, 'Meta', None), 'serialization_options', {}
                ).get(field_name, {})
                field_type = field_options.get('field_type', FormDescription.FIELD_TYPE_MAP.get(field.__class__))
                if not field_type:
                    raise ImproperlyConfigured(
                        "Field type '{}' not recognized for registration extension field '{}'.".format(
                            field_type,
                            field_name
                        )
                    )
                form_desc.add_field(
                    field_name, label=field.label,
                    default=field_options.get('default'),
                    field_type=field_options.get('field_type', FormDescription.FIELD_TYPE_MAP.get(field.__class__)),
                    placeholder=field.initial, instructions=field.help_text, required=field.required,
                    restrictions=restrictions,
                    options=getattr(field, 'choices', None), error_messages=field.error_messages,
                    include_default_option=field_options.get('include_default_option'),
                )

            # Extra fields configured in Django settings
            # may be required, optional, or hidden
            for field_name in self.EXTRA_FIELDS:
                if self._is_field_visible(field_name):
                    self.field_handlers[field_name](
                        form_desc,
                        required=self._is_field_required(field_name)
                    )
        else:
            # Go through the fields in the fields order and add them if they are required or visible
            for field_name in self.field_order:
                if field_name in self.DEFAULT_FIELDS:
                    self.field_handlers[field_name](form_desc, required=True)
                elif self._is_field_visible(field_name):
                    self.field_handlers[field_name](
                        form_desc,
                        required=self._is_field_required(field_name)
                    )

        return form_desc

    def _add_email_field(self, form_desc, required=True):
        """Add an email field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's email address.
        email_label = _(u"Email")

        # Translators: These instructions appear on the registration form, immediately
        # below a field meant to hold the user's email address.
        email_instructions = _(u"This is what you will use to login.")

        form_desc.add_field(
            "email",
            field_type="email",
            label=email_label,
            instructions=email_instructions,
            restrictions={
                "min_length": accounts.EMAIL_MIN_LENGTH,
                "max_length": accounts.EMAIL_MAX_LENGTH,
            },
            required=required
        )

    def _add_confirm_email_field(self, form_desc, required=True):
        """Add an email confirmation field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to confirm the user's email address.
        email_label = _(u"Confirm Email")

        error_msg = accounts.REQUIRED_FIELD_CONFIRM_EMAIL_MSG

        form_desc.add_field(
            "confirm_email",
            label=email_label,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_name_field(self, form_desc, required=True):
        """Add a name field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's full name.
        name_label = _(u"Full Name")

        # Translators: These instructions appear on the registration form, immediately
        # below a field meant to hold the user's full name.
        name_instructions = _(u"This name will be used on any certificates that you earn.")

        form_desc.add_field(
            "name",
            label=name_label,
            instructions=name_instructions,
            restrictions={
                "max_length": accounts.NAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_username_field(self, form_desc, required=True):
        """Add a username field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's public username.
        username_label = _(u"Public Username")

        username_instructions = _(
            # Translators: These instructions appear on the registration form, immediately
            # below a field meant to hold the user's public username.
            u"The name that will identify you in your courses. "
            u"It cannot be changed later."
        )
        form_desc.add_field(
            "username",
            label=username_label,
            instructions=username_instructions,
            restrictions={
                "min_length": accounts.USERNAME_MIN_LENGTH,
                "max_length": accounts.USERNAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_password_field(self, form_desc, required=True):
        """Add a password field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's password.
        password_label = _(u"Password")

        form_desc.add_field(
            "password",
            label=password_label,
            field_type="password",
            instructions=password_validators_instruction_texts(),
            restrictions=password_validators_restrictions(),
            required=required
        )

    def _add_level_of_education_field(self, form_desc, required=True):
        """Add a level of education field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's highest completed level of education.
        education_level_label = _(u"Highest level of education completed")
        error_msg = accounts.REQUIRED_FIELD_LEVEL_OF_EDUCATION_MSG

        # The labels are marked for translation in UserProfile model definition.
        options = [(name, _(label)) for name, label in UserProfile.LEVEL_OF_EDUCATION_CHOICES]
        form_desc.add_field(
            "level_of_education",
            label=education_level_label,
            field_type="select",
            options=options,
            include_default_option=True,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_gender_field(self, form_desc, required=True):
        """Add a gender field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's gender.
        gender_label = _(u"Gender")

        # The labels are marked for translation in UserProfile model definition.
        options = [(name, _(label)) for name, label in UserProfile.GENDER_CHOICES]
        form_desc.add_field(
            "gender",
            label=gender_label,
            field_type="select",
            options=options,
            include_default_option=True,
            required=required
        )

    def _add_year_of_birth_field(self, form_desc, required=True):
        """Add a year of birth field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's year of birth.
        yob_label = _(u"Year of birth")

        options = [(unicode(year), unicode(year)) for year in UserProfile.VALID_YEARS]
        form_desc.add_field(
            "year_of_birth",
            label=yob_label,
            field_type="select",
            options=options,
            include_default_option=True,
            required=required
        )

    def _add_field_with_configurable_select_options(self, field_name, field_label, form_desc, required=False):
        """Add a field to a form description.
            If select options are given for this field, it will be a select type
            otherwise it will be a text type.

        Arguments:
            field_name: name of field
            field_label: label for the field
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False

        """

        extra_field_options = configuration_helpers.get_value('EXTRA_FIELD_OPTIONS')
        if extra_field_options is None or extra_field_options.get(field_name) is None:
            field_type = "text"
            include_default_option = False
            options = None
            error_msg = ''
            exec("error_msg = accounts.REQUIRED_FIELD_%s_TEXT_MSG" % (field_name.upper()))
        else:
            field_type = "select"
            include_default_option = True
            field_options = extra_field_options.get(field_name)
            options = [(unicode(option.lower()), option) for option in field_options]
            error_msg = ''
            exec("error_msg = accounts.REQUIRED_FIELD_%s_SELECT_MSG" % (field_name.upper()))

        form_desc.add_field(
            field_name,
            label=field_label,
            field_type=field_type,
            options=options,
            include_default_option=include_default_option,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_profession_field(self, form_desc, required=False):
        """Add a profession field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's profession
        profession_label = _("Profession")

        self._add_field_with_configurable_select_options('profession', profession_label, form_desc, required=required)

    def _add_specialty_field(self, form_desc, required=False):
        """Add a specialty field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's specialty
        specialty_label = _("Specialty")

        self._add_field_with_configurable_select_options('specialty', specialty_label, form_desc, required=required)

    def _add_mailing_address_field(self, form_desc, required=True):
        """Add a mailing address field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's mailing address.
        mailing_address_label = _(u"Mailing address")
        error_msg = accounts.REQUIRED_FIELD_MAILING_ADDRESS_MSG

        form_desc.add_field(
            "mailing_address",
            label=mailing_address_label,
            field_type="textarea",
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_goals_field(self, form_desc, required=True):
        """Add a goals field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This phrase appears above a field on the registration form
        # meant to hold the user's reasons for registering with edX.
        goals_label = _(u"Tell us why you're interested in {platform_name}").format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME)
        )
        error_msg = accounts.REQUIRED_FIELD_GOALS_MSG

        form_desc.add_field(
            "goals",
            label=goals_label,
            field_type="textarea",
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_city_field(self, form_desc, required=True):
        """Add a city field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the city in which they live.
        city_label = _(u"City")
        error_msg = accounts.REQUIRED_FIELD_CITY_MSG

        form_desc.add_field(
            "city",
            label=city_label,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_state_field(self, form_desc, required=False):
        """Add a State/Province/Region field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the State/Province/Region in which they live.
        state_label = _(u"State/Province/Region")

        form_desc.add_field(
            "state",
            label=state_label,
            required=required
        )

    def _add_company_field(self, form_desc, required=False):
        """Add a Company field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the Company
        company_label = _(u"Company")

        form_desc.add_field(
            "company",
            label=company_label,
            required=required
        )

    def _add_title_field(self, form_desc, required=False):
        """Add a Title field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the Title
        title_label = _(u"Title")

        form_desc.add_field(
            "title",
            label=title_label,
            required=required
        )

    def _add_job_title_field(self, form_desc, required=False):
        """Add a Job Title field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the Job Title
        job_title_label = _(u"Job Title")

        form_desc.add_field(
            "job_title",
            label=job_title_label,
            required=required
        )

    def _add_first_name_field(self, form_desc, required=False):
        """Add a First Name field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the First Name
        first_name_label = _(u"First Name")

        form_desc.add_field(
            "first_name",
            label=first_name_label,
            required=required
        )

    def _add_last_name_field(self, form_desc, required=False):
        """Add a Last Name field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to False
        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the First Name
        last_name_label = _(u"Last Name")

        form_desc.add_field(
            "last_name",
            label=last_name_label,
            required=required
        )

    def _add_country_field(self, form_desc, required=True):
        """Add a country field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the country in which the user lives.
        country_label = _(u"Country or Region of Residence")

        error_msg = accounts.REQUIRED_FIELD_COUNTRY_MSG

        # If we set a country code, make sure it's uppercase for the sake of the form.
        # pylint: disable=protected-access
        default_country = form_desc._field_overrides.get('country', {}).get('defaultValue')

        country_instructions = _(
            # Translators: These instructions appear on the registration form, immediately
            # below a field meant to hold the user's country.
            u"The country or region where you live."
        )
        if default_country:
            form_desc.override_field_properties(
                'country',
                default=default_country.upper()
            )

        form_desc.add_field(
            "country",
            label=country_label,
            instructions=country_instructions,
            field_type="select",
            options=list(countries),
            include_default_option=True,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_honor_code_field(self, form_desc, required=True):
        """Add an honor code field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """

        separate_honor_and_tos = self._is_field_visible("terms_of_service")
        # Separate terms of service and honor code checkboxes
        if separate_honor_and_tos:
            terms_label = _(u"Honor Code")
            terms_link = marketing_link("HONOR")

        # Combine terms of service and honor code checkboxes
        else:
            # Translators: This is a legal document users must agree to
            # in order to register a new account.
            terms_label = _(u"Terms of Service and Honor Code")
            terms_link = marketing_link("HONOR")

        # Translators: "Terms of Service" is a legal document users must agree to
        # in order to register a new account.
        label = Text(_(
            u"I agree to the {platform_name} {terms_of_service_link_start}{terms_of_service}{terms_of_service_link_end}"
        )).format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
            terms_of_service=terms_label,
            terms_of_service_link_start=HTML("<a href='{terms_link}' rel='noopener' target='_blank'>").format(
                terms_link=terms_link
            ),
            terms_of_service_link_end=HTML("</a>"),
        )

        # Translators: "Terms of Service" is a legal document users must agree to
        # in order to register a new account.
        error_msg = _(u"You must agree to the {platform_name} {terms_of_service}").format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
            terms_of_service=terms_label
        )
        field_type = 'checkbox'

        if not separate_honor_and_tos:
            current_request = crum.get_current_request()

            field_type = 'plaintext'

            pp_link = marketing_link("PRIVACY")
            label = Text(_(
                u"By creating an account with {platform_name}, you agree \
                  to abide by our {platform_name} \
                  {terms_of_service_link_start}{terms_of_service}{terms_of_service_link_end} \
                  and agree to our {privacy_policy_link_start}Privacy Policy{privacy_policy_link_end}."
            )).format(
                platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
                terms_of_service=terms_label,
                terms_of_service_link_start=HTML("<a href='{terms_url}' rel='noopener' target='_blank'>").format(
                    terms_url=terms_link
                ),
                terms_of_service_link_end=HTML("</a>"),
                privacy_policy_link_start=HTML("<a href='{pp_url}' rel='noopener' target='_blank'>").format(
                    pp_url=pp_link
                ),
                privacy_policy_link_end=HTML("</a>"),
            )

        form_desc.add_field(
            "honor_code",
            label=label,
            field_type=field_type,
            default=False,
            required=required,
            error_messages={
                "required": error_msg
            },
        )

    def _add_terms_of_service_field(self, form_desc, required=True):
        """Add a terms of service field to a form description.
        Arguments:
            form_desc: A form description
        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """
        # Translators: This is a legal document users must agree to
        # in order to register a new account.
        terms_label = _(u"Terms of Service")
        terms_link = marketing_link("TOS")

        # Translators: "Terms of service" is a legal document users must agree to
        # in order to register a new account.
        label = Text(_(u"I agree to the {platform_name} {tos_link_start}{terms_of_service}{tos_link_end}")).format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
            terms_of_service=terms_label,
            tos_link_start=HTML("<a href='{terms_link}' rel='noopener' target='_blank'>").format(terms_link=terms_link),
            tos_link_end=HTML("</a>"),
        )

        # Translators: "Terms of service" is a legal document users must agree to
        # in order to register a new account.
        error_msg = _(u"You must agree to the {platform_name} {terms_of_service}").format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
            terms_of_service=terms_label
        )

        form_desc.add_field(
            "terms_of_service",
            label=label,
            field_type="checkbox",
            default=False,
            required=required,
            error_messages={
                "required": error_msg
            },
        )

    def _apply_third_party_auth_overrides(self, request, form_desc):
        """Modify the registration form if the user has authenticated with a third-party provider.
        If a user has successfully authenticated with a third-party provider,
        but does not yet have an account with EdX, we want to fill in
        the registration form with any info that we get from the
        provider.
        This will also hide the password field, since we assign users a default
        (random) password on the assumption that they will be using
        third-party auth to log in.
        Arguments:
            request (HttpRequest): The request for the registration form, used
                to determine if the user has successfully authenticated
                with a third-party provider.
            form_desc (FormDescription): The registration form description
        """
        if third_party_auth.is_enabled():
            running_pipeline = third_party_auth.pipeline.get(request)
            if running_pipeline:
                current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)

                if current_provider:
                    # Override username / email / full name
                    field_overrides = current_provider.get_register_form_data(
                        running_pipeline.get('kwargs')
                    )

                    # When the TPA Provider is configured to skip the registration form and we are in an
                    # enterprise context, we need to hide all fields except for terms of service and
                    # ensure that the user explicitly checks that field.
                    hide_registration_fields_except_tos = (
                        (
                            current_provider.skip_registration_form and enterprise_customer_for_request(request)
                        ) or current_provider.sync_learner_profile_data
                    )

                    for field_name in self.DEFAULT_FIELDS + self.EXTRA_FIELDS:
                        if field_name in field_overrides:
                            form_desc.override_field_properties(
                                field_name, default=field_overrides[field_name]
                            )

                            if (field_name not in ['terms_of_service', 'honor_code']
                                    and field_overrides[field_name]
                                    and hide_registration_fields_except_tos):

                                form_desc.override_field_properties(
                                    field_name,
                                    field_type="hidden",
                                    label="",
                                    instructions="",
                                )

                    # Hide the password field
                    form_desc.override_field_properties(
                        "password",
                        default="",
                        field_type="hidden",
                        required=False,
                        label="",
                        instructions="",
                        restrictions={}
                    )
                    # used to identify that request is running third party social auth
                    form_desc.add_field(
                        "social_auth_provider",
                        field_type="hidden",
                        label="",
                        default=current_provider.name if current_provider.name else "Third Party",
                        required=False,
                    )
