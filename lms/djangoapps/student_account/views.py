""" Views for a student's account information. """

import logging

from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseBadRequest,
    HttpResponseForbidden
)
from django.core.mail import send_mail
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response, render_to_string
from microsite_configuration import microsite

from user_api.api import account as account_api
from user_api.api import profile as profile_api
from util.bad_request_rate_limiter import BadRequestRateLimiter


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
