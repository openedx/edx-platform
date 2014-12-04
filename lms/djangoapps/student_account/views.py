""" Views for a student's account information. """

import logging
import json
from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
)
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response, render_to_string
from microsite_configuration import microsite
import third_party_auth
from external_auth.login_and_register import (
    login as external_auth_login,
    register as external_auth_register
)
from student.views import (
    signin_user as old_login_view,
    register_user as old_register_view
)

from user_api.api import account as account_api
from user_api.api import profile as profile_api
from util.bad_request_rate_limiter import BadRequestRateLimiter

from student_account.helpers import auth_pipeline_urls


AUDIT_LOG = logging.getLogger("audit")


@login_required
@require_http_methods(['GET'])
def index(request):
    """Render the account info page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the index page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        GET /account

    """
    return render_to_response(
        'student_account/index.html', {
            'disable_courseware_js': True,
        }
    )


@require_http_methods(['GET'])
@ensure_csrf_cookie
def login_and_registration_form(request, initial_mode="login"):
    """Render the combined login/registration form, defaulting to login

    This relies on the JS to asynchronously load the actual form from
    the user_api.

    Keyword Args:
        initial_mode (string): Either "login" or "register".

    """
    # If we're already logged in, redirect to the dashboard
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    # If this is a microsite, revert to the old login/registration pages.
    # We need to do this for now to support existing themes.
    if microsite.is_request_in_microsite():
        if initial_mode == "login":
            return old_login_view(request)
        elif initial_mode == "register":
            return old_register_view(request)

    # Allow external auth to intercept and handle the request
    ext_auth_response = _external_auth_intercept(request, initial_mode)
    if ext_auth_response is not None:
        return ext_auth_response

    # Otherwise, render the combined login/registration page
    context = {
        'disable_courseware_js': True,
        'initial_mode': initial_mode,
        'third_party_auth': json.dumps(_third_party_auth_context(request)),
        'platform_name': settings.PLATFORM_NAME,
        'responsive': True
    }

    return render_to_response('student_account/login_and_register.html', context)


@login_required
@require_http_methods(['POST'])
@ensure_csrf_cookie
def email_change_request_handler(request):
    """Handle a request to change the user's email address.

    Sends an email to the newly specified address containing a link
    to a confirmation page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the confirmation email was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 400 if the format of the new email is incorrect, or if
            an email change is requested for a user which does not exist
        HttpResponse: 401 if the provided password (in the form) is incorrect
        HttpResponse: 405 if using an unsupported HTTP method
        HttpResponse: 409 if the provided email is already in use

    Example usage:

        POST /account/email

    """
    username = request.user.username
    password = request.POST.get('password')
    new_email = request.POST.get('email')

    if new_email is None:
        return HttpResponseBadRequest("Missing param 'email'")
    if password is None:
        return HttpResponseBadRequest("Missing param 'password'")

    old_email = profile_api.profile_info(username)['email']

    try:
        key = account_api.request_email_change(username, new_email, password)
    except (account_api.AccountEmailInvalid, account_api.AccountUserNotFound):
        return HttpResponseBadRequest()
    except account_api.AccountEmailAlreadyExists:
        return HttpResponse(status=409)
    except account_api.AccountNotAuthorized:
        return HttpResponse(status=401)

    context = {
        'key': key,
        'old_email': old_email,
        'new_email': new_email,
    }

    subject = render_to_string('student_account/emails/email_change_request/subject_line.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('student_account/emails/email_change_request/message_body.txt', context)

    from_address = microsite.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )

    # Send a confirmation email to the new address containing the activation key
    send_mail(subject, message, from_address, [new_email])

    return HttpResponse(status=200)


@login_required
@require_http_methods(['GET'])
def email_change_confirmation_handler(request, key):
    """Complete a change of the user's email address.

    This is called when the activation link included in the confirmation
    email is clicked.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the email change is successful, the activation key
            is invalid, the new email is already in use, or the
            user to which the email change will be applied does
            not exist
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        GET /account/email/confirmation/{key}

    """
    try:
        old_email, new_email = account_api.confirm_email_change(key)
    except account_api.AccountNotAuthorized:
        return render_to_response(
            'student_account/email_change_failed.html', {
                'disable_courseware_js': True,
                'error': 'key_invalid',
            }
        )
    except account_api.AccountEmailAlreadyExists:
        return render_to_response(
            'student_account/email_change_failed.html', {
                'disable_courseware_js': True,
                'error': 'email_used',
            }
        )
    except account_api.AccountInternalError:
        return render_to_response(
            'student_account/email_change_failed.html', {
                'disable_courseware_js': True,
                'error': 'internal',
            }
        )

    context = {
        'old_email': old_email,
        'new_email': new_email,
    }

    subject = render_to_string('student_account/emails/email_change_confirmation/subject_line.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('student_account/emails/email_change_confirmation/message_body.txt', context)

    from_address = microsite.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )

    # Notify both old and new emails of the change
    send_mail(subject, message, from_address, [old_email, new_email])

    return render_to_response(
        'student_account/email_change_successful.html', {
            'disable_courseware_js': True,
        }
    )


@require_http_methods(['POST'])
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
        HttpResponse: 400 if there is no 'email' POST parameter, or if no user with
            the provided email exists
        HttpResponse: 403 if the client has been rate limited
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        POST /account/password

    """
    limiter = BadRequestRateLimiter()
    if limiter.is_rate_limit_exceeded(request):
        AUDIT_LOG.warning("Password reset rate limit exceeded")
        return HttpResponseForbidden()

    user = request.user
    # Prefer logged-in user's email
    email = user.email if user.is_authenticated() else request.POST.get('email')

    if email:
        try:
            account_api.request_password_change(email, request.get_host(), request.is_secure())
        except account_api.AccountUserNotFound:
            AUDIT_LOG.info("Invalid password reset attempt")
            # Increment the rate limit counter
            limiter.tick_bad_request_counter(request)

            return HttpResponseBadRequest("No active user with the provided email address exists.")

        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest("No email address provided.")


def _third_party_auth_context(request):
    """Context for third party auth providers and the currently running pipeline.

    Arguments:
        request (HttpRequest): The request, used to determine if a pipeline
            is currently running.

    Returns:
        dict

    """
    context = {
        "currentProvider": None,
        "providers": []
    }

    course_id = request.GET.get("course_id")
    redirect_to = request.GET.get("next")
    login_urls = auth_pipeline_urls(
        third_party_auth.pipeline.AUTH_ENTRY_LOGIN,
        course_id=course_id,
        redirect_url=redirect_to
    )
    register_urls = auth_pipeline_urls(
        third_party_auth.pipeline.AUTH_ENTRY_REGISTER,
        course_id=course_id
    )

    if third_party_auth.is_enabled():
        context["providers"] = [
            {
                "name": enabled.NAME,
                "iconClass": enabled.ICON_CLASS,
                "loginUrl": login_urls[enabled.NAME],
                "registerUrl": register_urls[enabled.NAME]
            }
            for enabled in third_party_auth.provider.Registry.enabled()
        ]

        running_pipeline = third_party_auth.pipeline.get(request)
        if running_pipeline is not None:
            current_provider = third_party_auth.provider.Registry.get_by_backend_name(
                running_pipeline.get('backend')
            )
            context["currentProvider"] = current_provider.NAME

    return context


def _external_auth_intercept(request, mode):
    """Allow external auth to intercept a login/registration request.

    Arguments:
        request (Request): The original request.
        mode (str): Either "login" or "register"

    Returns:
        Response or None

    """
    if mode == "login":
        return external_auth_login(request)
    elif mode == "register":
        return external_auth_register(request)
