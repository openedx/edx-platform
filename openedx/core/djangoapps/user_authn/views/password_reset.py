""" Handles password resets logic. """

from django import forms

from django.contrib.auth.forms import PasswordResetForm

from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from edx_ace import ace
from edx_ace.recipient import Recipient
from rest_framework.views import APIView

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_request, get_current_site
from openedx.core.djangoapps.user_api import accounts, errors, helpers
from openedx.core.djangoapps.user_api.accounts.utils import is_secondary_email_feature_enabled
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.djangoapps.user_authn.message_types import PasswordReset

from student.models import AccountRecovery
from student.forms import send_account_recovery_email_for_user


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
    # pylint: disable=no-member
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


def send_password_reset_email_for_user(user, request, preferred_email=None):
    """
    Send out a password reset email for the given user.

    Arguments:
        user (User): Django User object
        request (HttpRequest): Django request object
        preferred_email (str): Send email to this address if present, otherwise fallback to user's email address.
    """
    site = get_current_site()
    message_context = get_base_template_context(site)
    message_context.update({
        'request': request,  # Used by google_analytics_tracking_pixel
        # TODO: This overrides `platform_name` from `get_base_template_context` to make the tests passes
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'reset_link': '{protocol}://{site}{link}?track=pwreset'.format(
            protocol='https' if request.is_secure() else 'http',
            site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            link=reverse('password_reset_confirm', kwargs={
                'uidb36': int_to_base36(user.id),
                'token': default_token_generator.make_token(user),
            }),
        )
    })

    msg = PasswordReset().personalize(
        recipient=Recipient(user.username, preferred_email or user.email),
        language=get_user_preference(user, LANGUAGE_KEY),
        user_context=message_context,
    )
    ace.send(msg)


class PasswordResetFormNoActive(PasswordResetForm):
    """
    A modified version of the default Django password reset form to handle
    unknown or unusable email addresses without leaking data.
    """
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }

    is_account_recovery = True
    users_cache = []

    def clean_email(self):
        """
        This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except removing the requirement of active users
        Validates that a user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)

        if not self.users_cache and is_secondary_email_feature_enabled():
            # Check if user has entered the secondary email.
            self.users_cache = User.objects.filter(
                id__in=AccountRecovery.objects.filter(secondary_email__iexact=email, is_active=True).values_list('user')
            )
            self.is_account_recovery = not bool(self.users_cache)

        if not self.users_cache:
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password.startswith(UNUSABLE_PASSWORD_PREFIX))
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(self,  # pylint: disable=arguments-differ
             use_https=False,
             token_generator=default_token_generator,
             request=None,
             **_kwargs):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        for user in self.users_cache:
            if self.is_account_recovery:
                send_password_reset_email_for_user(user, request)
            else:
                send_account_recovery_email_for_user(user, request, user.account_recovery.secondary_email)


class PasswordResetView(APIView):
    """HTTP end-point for GETting a description of the password reset form. """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return HttpResponse(get_password_reset_form().to_json(), content_type="application/json")


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def request_password_change(email, is_secure):
    """Email a single-use link for performing a password reset.

    Users must confirm the password change before we update their information.

    Args:
        email (str): An email address
        orig_host (str): An originating host, extracted from a request with get_host
        is_secure (bool): Whether the request was made with HTTPS

    Returns:
        None

    Raises:
        errors.UserNotFound
        AccountRequestError
        errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    # Binding data to a form requires that the data be passed as a dictionary
    # to the Form class constructor.
    form = PasswordResetFormNoActive({'email': email})

    # Validate that a user exists with the given email address.
    if form.is_valid():
        # Generate a single-use link for performing a password reset
        # and email it to the user.
        form.save(
            from_email=configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
            use_https=is_secure,
            request=get_current_request(),
        )
    else:
        # No user with the provided email address exists.
        raise errors.UserNotFound
