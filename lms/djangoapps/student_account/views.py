""" Views for a student's account information. """

import logging
import json
from ipware.ip import get_ip

from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
)
from django.shortcuts import redirect
from django.http import HttpRequest
from django.core.urlresolvers import reverse, resolve
from django.utils.translation import ugettext as _
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from edxmako.shortcuts import render_to_response
from microsite_configuration import microsite
from embargo import api as embargo_api
import third_party_auth
from external_auth.login_and_register import (
    login as external_auth_login,
    register as external_auth_register
)
from student.views import (
    signin_user as old_login_view,
    register_user as old_register_view
)

from openedx.core.djangoapps.user_api.accounts.api import request_password_change
from openedx.core.djangoapps.user_api.errors import UserNotFound
from util.bad_request_rate_limiter import BadRequestRateLimiter

from student_account.helpers import auth_pipeline_urls


AUDIT_LOG = logging.getLogger("audit")


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

    # Retrieve the form descriptions from the user API
    form_descriptions = _get_form_descriptions(request)

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
        'responsive': True,

        # Include form descriptions retrieved from the user API.
        # We could have the JS client make these requests directly,
        # but we include them in the initial page load to avoid
        # the additional round-trip to the server.
        'login_form_desc': form_descriptions['login'],
        'registration_form_desc': form_descriptions['registration'],
        'password_reset_form_desc': form_descriptions['password_reset'],

        # We need to pass these parameters so that the header's
        # "Sign In" button preserves the querystring params.
        'enrollment_action': request.GET.get('enrollment_action'),
        'course_id': request.GET.get('course_id'),
        'course_mode': request.GET.get('course_mode'),
    }

    return render_to_response('student_account/login_and_register.html', context)


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
            request_password_change(email, request.get_host(), request.is_secure())
        except UserNotFound:
            AUDIT_LOG.info("Invalid password reset attempt")
            # Increment the rate limit counter
            limiter.tick_bad_request_counter(request)

            return HttpResponseBadRequest(_("No user with the provided email address exists."))

        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest(_("No email address provided."))


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
    email_opt_in = request.GET.get('email_opt_in')
    redirect_to = request.GET.get("next")

    # Check if the user is trying to enroll in a course
    # that they don't have access to based on country
    # access rules.
    #
    # If so, set the redirect URL to the blocked page.
    # We need to set it here, rather than redirecting
    # from within the pipeline, because a redirect
    # from the pipeline can prevent users
    # from completing the authentication process.
    #
    # Note that we can't check the user's country
    # profile at this point, since the user hasn't
    # authenticated.  If the user ends up being blocked
    # by their country preference, we let them enroll;
    # they'll still be blocked when they try to access
    # the courseware.
    if course_id:
        try:
            course_key = CourseKey.from_string(course_id)
            redirect_url = embargo_api.redirect_if_blocked(
                course_key,
                ip_address=get_ip(request),
                url=request.path
            )
            if redirect_url:
                redirect_to = embargo_api.message_url_path(course_key, "enrollment")
        except InvalidKeyError:
            pass

    login_urls = auth_pipeline_urls(
        third_party_auth.pipeline.AUTH_ENTRY_LOGIN,
        course_id=course_id,
        email_opt_in=email_opt_in,
        redirect_url=redirect_to
    )
    register_urls = auth_pipeline_urls(
        third_party_auth.pipeline.AUTH_ENTRY_REGISTER,
        course_id=course_id,
        email_opt_in=email_opt_in,
        redirect_url=redirect_to
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


def _get_form_descriptions(request):
    """Retrieve form descriptions from the user API.

    Arguments:
        request (HttpRequest): The original request, used to retrieve session info.

    Returns:
        dict: Keys are 'login', 'registration', and 'password_reset';
            values are the JSON-serialized form descriptions.

    """
    return {
        'login': _local_server_get('/user_api/v1/account/login_session/', request.session),
        'registration': _local_server_get('/user_api/v1/account/registration/', request.session),
        'password_reset': _local_server_get('/user_api/v1/account/password_reset/', request.session)
    }


def _local_server_get(url, session):
    """Simulate a server-server GET request for an in-process API.

    Arguments:
        url (str): The URL of the request (excluding the protocol and domain)
        session (SessionStore): The session of the original request,
            used to get past the CSRF checks.

    Returns:
        str: The content of the response

    """
    # Since the user API is currently run in-process,
    # we simulate the server-server API call by constructing
    # our own request object.  We don't need to include much
    # information in the request except for the session
    # (to get past through CSRF validation)
    request = HttpRequest()
    request.method = "GET"
    request.session = session

    # Call the Django view function, simulating
    # the server-server API call
    view, args, kwargs = resolve(url)
    response = view(request, *args, **kwargs)

    # Return the content of the response
    return response.content


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
