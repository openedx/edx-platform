"""
Login form and views
"""

from django import forms
from django.urls import reverse
from django.utils.translation import ugettext as _

from common.djangoapps.util.password_policy_validators import DEFAULT_MAX_PASSWORD_LENGTH
from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.core.djangoapps.user_authn.views.login_form import _apply_third_party_auth_overrides


def get_login_session_form_override(request):
    """
    Return a description of the login form.

    This is used as an override for a core method.
    Original Method: edx-platform/openedx/core/djangoapps/user_authn/views/login_form.get_login_session_form

    Changes from core are:
    1. Added placeholder for email
    2. Removed email instructions
    3. Added placeholder for password
    4. Added ModelChoiceField support to handle foreign key field

    Returns:
        FormDescription

    """
    FormDescription.FIELD_TYPE_MAP[forms.ModelChoiceField] = 'select'
    form_desc = FormDescription('post', reverse('user_api_login_session'))
    _apply_third_party_auth_overrides(request, form_desc)

    placeholder_and_label = _('Email')

    form_desc.add_field(
        'email',
        field_type='email',
        label=placeholder_and_label,
        placeholder=placeholder_and_label,
        restrictions={
            'min_length': accounts.EMAIL_MIN_LENGTH,
            'max_length': accounts.EMAIL_MAX_LENGTH,
        }
    )

    # Translators: This label appears above a field on the login form
    # meant to hold the user's password.
    placeholder_and_label = _(u'Password')

    form_desc.add_field(
        'password',
        label=placeholder_and_label,
        placeholder=placeholder_and_label,
        field_type='password',
        restrictions={'max_length': DEFAULT_MAX_PASSWORD_LENGTH}
    )

    return form_desc
