"""
Password reset forms and views.
"""

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_api.helpers import FormDescription


def get_password_reset_form_override():
    """
    Return a description of the password reset form.

    This is used as an override for a core method.
    Original Method: edx-platform.openedx.core.djangoapps.user_authn.views.password_reset.get_password_reset_form

    Changes from core are:
    1. Added placeholder for email

    Returns:
        FormDescription

    """

    form_desc = FormDescription('post', reverse('password_change_request'))

    # Translators: This label appears above a field on the password reset
    # form meant to hold the user's email address.
    email_label = _(u'Email')

    # Translators: This example email address is used as a placeholder in
    # a field on the password reset form meant to hold the user's email address.
    email_placeholder = _(u'Email')

    form_desc.add_field(
        'email',
        field_type='email',
        label=email_label,
        placeholder=email_placeholder,
        restrictions={
            'min_length': accounts.EMAIL_MIN_LENGTH,
            'max_length': accounts.EMAIL_MAX_LENGTH,
        }
    )

    return form_desc
