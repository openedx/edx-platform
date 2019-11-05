"""
User Apis.
"""
from __future__ import absolute_import

import copy

import crum
import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import ugettext as _
from django_countries import countries

import third_party_auth
from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from student.models import UserProfile
from util.password_policy_validators import (
    DEFAULT_MAX_PASSWORD_LENGTH,
    password_validators_instruction_texts,
    password_validators_restrictions
)


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

    # Translators: This label appears above a field on the login form
    # meant to hold the user's password.
    password_label = _(u"Password")

    form_desc.add_field(
        "password",
        label=password_label,
        field_type="password",
        restrictions={'max_length': DEFAULT_MAX_PASSWORD_LENGTH}
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
