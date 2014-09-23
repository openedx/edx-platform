""" Views for a student's account information. """

from django.conf import settings
from django.http import HttpResponse, QueryDict
from django.core.mail import send_mail
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response, render_to_string
from microsite_configuration import microsite
from user_api.api import account as account_api
from user_api.api import profile as profile_api


@login_required
@require_http_methods(['GET'])
def index(request):
    """Render the account info page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200

    Example usage:

        GET /account

    """
    return render_to_response(
        'student_account/index.html', {
            'disable_courseware_js': True,
        }
    )


@login_required
@require_http_methods(['PUT'])
@ensure_csrf_cookie
def email_change_request_handler(request):
    """Handle a request to change the user's email address.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 204, if the confirmation email was sent successfully
        HttpResponse: 401, if authorization is refused for the provided credentials

    Example usage:

        PUT /account/email_change_request

    """
    put = QueryDict(request.body)
    user = request.user
    password = put.get('password')

    if not user.check_password(password):
        return HttpResponse(status=401)

    username = user.username
    old_email = profile_api.profile_info(username)['email']
    new_email = put.get('new_email')

    key = account_api.request_email_change(username, new_email, password)

    context = {
        'key': key,
        'old_email': old_email,
        'new_email': new_email
    }

    subject = render_to_string('emails/email_change_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/email_change.txt', context)

    from_address = microsite.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )

    # Email new address
    send_mail(subject, message, from_address, [new_email])

    # A 204 is intended to allow input for actions to take place
    # without causing a change to the user agent's active document view.
    return HttpResponse(status=204)


@login_required
@require_http_methods(['GET'])
def email_change_confirmation_handler(request, key):
    """Complete a change of the user's email address.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200

    Example usage:

        POST /account/email_change_confirm/{key}

    """
    pass
