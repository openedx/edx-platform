""" Password reset logic and views . """

import logging
from django import forms

from django.contrib.auth.forms import PasswordResetForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import password_reset_confirm
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import base36_to_int, int_to_base36, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from edx_ace import ace
from edx_ace.recipient import Recipient
from edxmako.shortcuts import render_to_string
from eventtracking import tracker
from rest_framework.views import APIView

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.oauth_dispatch.api import destroy_oauth_tokens
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_request, get_current_site
from openedx.core.djangoapps.user_api import accounts, errors, helpers
from openedx.core.djangoapps.user_api.accounts.utils import is_secondary_email_feature_enabled
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.core.djangoapps.user_api.models import UserRetirementRequest
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, SYSTEM_MAINTENANCE_MSG, waffle
from openedx.core.djangoapps.user_authn.message_types import PasswordReset
from openedx.core.djangolib.markup import HTML

from student.models import AccountRecovery
from student.forms import send_account_recovery_email_for_user

from util.json_request import JsonResponse
from util.password_policy_validators import normalize_password, validate_password
from util.request_rate_limiter import BadRequestRateLimiter, PasswordResetEmailRateLimiter


SETTING_CHANGE_INITIATED = 'edx.user.settings.change_initiated'

# Maintaining this naming for backwards compatibility.
log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")


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


@csrf_exempt
@require_POST
def password_reset(request):
    """
    Attempts to send a password reset e-mail.
    """
    # Add some rate limiting here by re-using the RateLimitMixin as a helper class
    limiter = BadRequestRateLimiter()
    if limiter.is_rate_limit_exceeded(request):
        AUDIT_LOG.warning("Rate limit exceeded in password_reset")
        return HttpResponseForbidden()

    form = PasswordResetFormNoActive(request.POST)
    if form.is_valid():
        form.save(use_https=request.is_secure(),
                  from_email=configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
                  request=request)
        # When password change is complete, a "edx.user.settings.changed" event will be emitted.
        # But because changing the password is multi-step, we also emit an event here so that we can
        # track where the request was initiated.
        tracker.emit(
            SETTING_CHANGE_INITIATED,
            {
                "setting": "password",
                "old": None,
                "new": None,
                "user_id": request.user.id,
            }
        )
        destroy_oauth_tokens(request.user)
    else:
        # bad user? tick the rate limiter counter
        AUDIT_LOG.info("Bad password_reset user passed in.")
        limiter.tick_request_counter(request)

    return JsonResponse({
        'success': True,
        'value': render_to_string('registration/password_reset_done.html', {}),
    })


def _uidb36_to_uidb64(uidb36):
    """
    Needed to support old password reset URLs that use base36-encoded user IDs
    https://github.com/django/django/commit/1184d077893ff1bc947e45b00a4d565f3df81776#diff-c571286052438b2e3190f8db8331a92bR231
    Args:
        uidb36: base36-encoded user ID

    Returns: base64-encoded user ID. Otherwise returns a dummy, invalid ID
    """
    try:
        uidb64 = force_text(urlsafe_base64_encode(force_bytes(base36_to_int(uidb36))))
    except ValueError:
        uidb64 = '1'  # dummy invalid ID (incorrect padding for base64)
    return uidb64


# pylint: disable=too-many-statements
def password_reset_confirm_wrapper(request, uidb36=None, token=None):
    """
    A wrapper around django.contrib.auth.views.password_reset_confirm.
    Needed because we want to set the user as active at this step.
    We also optionally do some additional password policy checks.
    """
    # convert old-style base36-encoded user id to base64
    uidb64 = _uidb36_to_uidb64(uidb36)
    platform_name = {
        "platform_name": configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
    }

    # User can not get this link unless account recovery feature is enabled.
    if 'is_account_recovery' in request.GET and not is_secondary_email_feature_enabled():
        raise Http404

    try:
        uid_int = base36_to_int(uidb36)
        if request.user.is_authenticated and request.user.id != uid_int:
            raise Http404

        user = User.objects.get(id=uid_int)
    except (ValueError, User.DoesNotExist):
        # if there's any error getting a user, just let django's
        # password_reset_confirm function handle it.
        return password_reset_confirm(
            request, uidb64=uidb64, token=token, extra_context=platform_name
        )

    if UserRetirementRequest.has_user_requested_retirement(user):
        # Refuse to reset the password of any user that has requested retirement.
        context = {
            'validlink': True,
            'form': None,
            'title': _('Password reset unsuccessful'),
            'err_msg': _('Error in resetting your password.'),
        }
        context.update(platform_name)
        return TemplateResponse(
            request, 'registration/password_reset_confirm.html', context
        )

    if waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        context = {
            'validlink': False,
            'form': None,
            'title': _('Password reset unsuccessful'),
            'err_msg': SYSTEM_MAINTENANCE_MSG,
        }
        context.update(platform_name)
        return TemplateResponse(
            request, 'registration/password_reset_confirm.html', context
        )

    if request.method == 'POST':
        # We have to make a copy of request.POST because it is a QueryDict object which is immutable until copied.
        # We have to use request.POST because the password_reset_confirm method takes in the request and a user's
        # password is set to the request.POST['new_password1'] field. We have to also normalize the new_password2
        # field so it passes the equivalence check that new_password1 == new_password2
        # In order to switch out of having to do this copy, we would want to move the normalize_password code into
        # a custom User model's set_password method to ensure it is always happening upon calling set_password.
        request.POST = request.POST.copy()
        request.POST['new_password1'] = normalize_password(request.POST['new_password1'])
        request.POST['new_password2'] = normalize_password(request.POST['new_password2'])

        password = request.POST['new_password1']

        try:
            validate_password(password, user=user)
        except ValidationError as err:
            # We have a password reset attempt which violates some security
            # policy, or any other validation. Use the existing Django template to communicate that
            # back to the user.
            context = {
                'validlink': True,
                'form': None,
                'title': _('Password reset unsuccessful'),
                'err_msg': ' '.join(err.messages),
            }
            context.update(platform_name)
            return TemplateResponse(
                request, 'registration/password_reset_confirm.html', context
            )

        if 'is_account_recovery' in request.GET:
            response = password_reset_confirm(
                request,
                uidb64=uidb64,
                token=token,
                extra_context=platform_name,
                template_name='registration/password_reset_confirm.html',
                post_reset_redirect='signin_user',
            )
        else:
            response = password_reset_confirm(
                request, uidb64=uidb64, token=token, extra_context=platform_name
            )

        # If password reset was unsuccessful a template response is returned (status_code 200).
        # Check if form is invalid then show an error to the user.
        # Note if password reset was successful we get response redirect (status_code 302).
        if response.status_code == 200:
            form_valid = response.context_data['form'].is_valid() if response.context_data['form'] else False
            if not form_valid:
                log.warning(
                    u'Unable to reset password for user [%s] because form is not valid. '
                    u'A possible cause is that the user had an invalid reset token',
                    user.username,
                )
                response.context_data['err_msg'] = _('Error in resetting your password. Please try again.')
                return response

        # get the updated user
        updated_user = User.objects.get(id=uid_int)
        if 'is_account_recovery' in request.GET:
            try:
                updated_user.email = updated_user.account_recovery.secondary_email
                updated_user.account_recovery.delete()
                # emit an event that the user changed their secondary email to the primary email
                tracker.emit(
                    SETTING_CHANGE_INITIATED,
                    {
                        "setting": "email",
                        "old": user.email,
                        "new": updated_user.email,
                        "user_id": updated_user.id,
                    }
                )
            except ObjectDoesNotExist:
                log.error(
                    u'Account recovery process initiated without AccountRecovery instance for user {username}'.format(
                        username=updated_user.username
                    )
                )

        updated_user.save()

        if response.status_code == 302 and 'is_account_recovery' in request.GET:
            messages.success(
                request,
                HTML(_(
                    u'{html_start}Password Creation Complete{html_end}'
                    u'Your password has been created. {bold_start}{email}{bold_end} is now your primary login email.'
                )).format(
                    support_url=configuration_helpers.get_value('SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK),
                    html_start=HTML('<p class="message-title">'),
                    html_end=HTML('</p>'),
                    bold_start=HTML('<b>'),
                    bold_end=HTML('</b>'),
                    email=updated_user.email,
                ),
                extra_tags='account-recovery aa-icon submission-success'
            )
    else:
        response = password_reset_confirm(
            request, uidb64=uidb64, token=token, extra_context=platform_name
        )

        response_was_successful = response.context_data.get('validlink')
        if response_was_successful and not user.is_active:
            user.is_active = True
            user.save()

    return response


def _get_user_from_email(email):
    """
    Find a user using given email and return it.

    Arguments:
        email (str): primary or secondary email address of the user.

    Raises:
        (User.ObjectNotFound): If no user is found with the given email.
        (User.MultipleObjectsReturned): If more than one user is found with the given email.

    Returns:
        User: Django user object.
    """
    try:
        return User.objects.get(email=email)
    except ObjectDoesNotExist:
        return User.objects.filter(
            id__in=AccountRecovery.objects.filter(secondary_email__iexact=email, is_active=True).values_list('user')
        ).get()


@require_POST
def password_change_request_handler(request):
    """Handle password change requests originating from the account page.

    Uses the Account API to email the user a link to the password reset page.

    Note:
        The next step in the password reset process (confirmation) is currently handled
        by student.views.password_reset_confirm_wrapper, a custom wrapper around Django's
        password reset confirmation view.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the email was sent successfully
        HttpResponse: 400 if there is no 'email' POST parameter
        HttpResponse: 403 if the client has been rate limited
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        POST /account/password

    """

    password_reset_email_limiter = PasswordResetEmailRateLimiter()

    if password_reset_email_limiter.is_rate_limit_exceeded(request):
        AUDIT_LOG.warning("Password reset rate limit exceeded")
        return HttpResponse(
            _("Your previous request is in progress, please try again in a few moments."),
            status=403
        )

    user = request.user
    # Prefer logged-in user's email
    email = user.email if user.is_authenticated else request.POST.get('email')

    if email:
        try:
            request_password_change(email, request.is_secure())
            user = user if user.is_authenticated else _get_user_from_email(email=email)
            destroy_oauth_tokens(user)
        except errors.UserNotFound:
            AUDIT_LOG.info("Invalid password reset attempt")
            # If enabled, send an email saying that a password reset was attempted, but that there is
            # no user associated with the email
            if configuration_helpers.get_value('ENABLE_PASSWORD_RESET_FAILURE_EMAIL',
                                               settings.FEATURES['ENABLE_PASSWORD_RESET_FAILURE_EMAIL']):
                site = get_current_site()
                message_context = get_base_template_context(site)

                message_context.update({
                    'failed': True,
                    'request': request,  # Used by google_analytics_tracking_pixel
                    'email_address': email,
                })

                msg = PasswordReset().personalize(
                    recipient=Recipient(username='', email_address=email),
                    language=settings.LANGUAGE_CODE,
                    user_context=message_context,
                )
                ace.send(msg)
        except errors.UserAPIInternalError as err:
            log.exception(u'Error occured during password change for user {email}: {error}'
                          .format(email=email, error=err))
            return HttpResponse(_("Some error occured during password change. Please try again"), status=500)

        password_reset_email_limiter.tick_request_counter(request)
        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest(_("No email address provided."))
