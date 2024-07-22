"""  # lint-amnesty, pylint: disable=cyclic-import
Student Views
"""


import datetime
import logging
import urllib.parse
import uuid
import requests
import json

import pytz

import time
import hmac
import base64
import hashlib

from collections import namedtuple
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.contrib.sites.models import Site
from django.core.validators import ValidationError, validate_email
from django.core.cache import cache
from openedx.core.djangoapps.enrollments.api import add_enrollment
from common.djangoapps.student.helpers import DISABLE_UNENROLL_CERT_STATES, cert_info, do_create_account
from django.core.exceptions import ObjectDoesNotExist
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from django.shortcuts import redirect, render

from openedx.core.djangoapps.enrollments.api import add_enrollment
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import int_to_base36
from openedx.core.djangoapps.enrollments.data import get_course_enrollments

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver  # lint-amnesty, pylint: disable=unused-import
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie  # lint-amnesty, pylint: disable=unused-import
from django.views.decorators.http import require_GET, require_http_methods, require_POST  # lint-amnesty, pylint: disable=unused-import
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_django_utils import monitoring as monitoring_utils
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser  # lint-amnesty, pylint: disable=wrong-import-order
from eventtracking import tracker
# Note that this lives in LMS, so this dependency should be refactored.
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from common.djangoapps.track import views as track_views
from lms.djangoapps.bulk_email.models import Optout
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.courses import get_courses, sort_by_announcement, sort_by_start_date
from common.djangoapps.edxmako.shortcuts import marketing_link, render_to_response, render_to_string  # lint-amnesty, pylint: disable=unused-import
from common.djangoapps.entitlements.models import CourseEntitlement
from common.djangoapps.student.helpers import get_next_url_for_login_page, get_redirect_url_with_host
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.catalog.utils import get_programs_with_type
from openedx.core.djangoapps.embargo import api as embargo_api
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.programs.models import ProgramsApiConfig  # lint-amnesty, pylint: disable=unused-import
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming import helpers as theming_helpers
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.tasks import send_activation_email
from openedx.core.djangoapps.user_authn.toggles import should_redirect_to_authn_microfrontend
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.features.enterprise_support.utils import is_enterprise_learner
from common.djangoapps.student.email_helpers import generate_activation_email_context
from common.djangoapps.student.helpers import DISABLE_UNENROLL_CERT_STATES, cert_info
from common.djangoapps.student.message_types import AccountActivation, EmailChange, EmailChangeConfirmation, RecoveryEmailCreate  # lint-amnesty, pylint: disable=line-too-long
from common.djangoapps.student.models import (  # lint-amnesty, pylint: disable=unused-import
    AccountRecovery,
    CourseEnrollment,
    PendingEmailChange,  # unimport:skip
    PendingSecondaryEmailChange,
    Registration,
    RegistrationCookieConfiguration,
    UnenrollmentNotAllowed,
    UserAttribute,
    UserProfile,
    UserSignupSource,
    UserStanding,
    create_comments_service_user,
    email_exists_or_retired
)
from common.djangoapps.student.signals import REFUND_ORDER
from common.djangoapps.util.db import outer_atomic
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.student.signals import USER_EMAIL_CHANGED
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger("edx.student")

AUDIT_LOG = logging.getLogger("audit")
ReverifyInfo = namedtuple(
    'ReverifyInfo',
    'course_id course_name course_number date status display'
)
SETTING_CHANGE_INITIATED = 'edx.user.settings.change_initiated'
# Used as the name of the user attribute for tracking affiliate registrations
REGISTRATION_AFFILIATE_ID = 'registration_affiliate_id'
REGISTRATION_UTM_PARAMETERS = {
    'utm_source': 'registration_utm_source',
    'utm_medium': 'registration_utm_medium',
    'utm_campaign': 'registration_utm_campaign',
    'utm_term': 'registration_utm_term',
    'utm_content': 'registration_utm_content',
}
REGISTRATION_UTM_CREATED_AT = 'registration_utm_created_at'
USER_ACCOUNT_ACTIVATED = 'edx.user.account.activated'


def csrf_token(context):
    """
    A csrf token that can be included in a form.
    """
    token = context.get('csrf_token', '')
    if token == 'NOTPROVIDED':
        return ''
    return (HTML('<div style="display:none"><input type="hidden"'
                 ' name="csrfmiddlewaretoken" value="{}" /></div>').format(Text(token)))


# NOTE: This view is not linked to directly--it is called from
# branding/views.py:index(), which is cached for anonymous users.
# This means that it should always return the same thing for anon
# users. (in particular, no switching based on query params allowed)
def index(request, extra_context=None, user=AnonymousUser()):
    """
    Render the edX main page.

    extra_context is used to allow immediate display of certain modal windows, eg signup.
    """
    if extra_context is None:
        extra_context = {}

    courses = get_courses(user)

    if configuration_helpers.get_value(
        "ENABLE_COURSE_SORTING_BY_START_DATE",
        settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"],
    ):
        courses = sort_by_start_date(courses)
    else:
        courses = sort_by_announcement(courses)

    context = {'courses': courses}

    context['homepage_overlay_html'] = configuration_helpers.get_value('homepage_overlay_html')

    # This appears to be an unused context parameter, at least for the master templates...
    context['show_partners'] = configuration_helpers.get_value('show_partners', True)

    # TO DISPLAY A YOUTUBE WELCOME VIDEO
    # 1) Change False to True
    context['show_homepage_promo_video'] = configuration_helpers.get_value('show_homepage_promo_video', False)

    # Maximum number of courses to display on the homepage.
    context['homepage_course_max'] = configuration_helpers.get_value(
        'HOMEPAGE_COURSE_MAX', settings.HOMEPAGE_COURSE_MAX
    )

    # 2) Add your video's YouTube ID (11 chars, eg "123456789xX"), or specify via site configuration
    # Note: This value should be moved into a configuration setting and plumbed-through to the
    # context via the site configuration workflow, versus living here
    youtube_video_id = configuration_helpers.get_value('homepage_promo_video_youtube_id', "your-youtube-id")
    context['homepage_promo_video_youtube_id'] = youtube_video_id

    # allow for theme override of the courses list
    context['courses_list'] = theming_helpers.get_template_path('courses_list.html')

    # Insert additional context for use in the template
    context.update(extra_context)

    # Add marketable programs to the context.
    context['programs_list'] = get_programs_with_type(request.site, include_hidden=False)

    return render_to_response('index.html', context)


def compose_activation_email(user, user_registration=None, route_enabled=False, profile_name='', redirect_url=None):
    """
    Construct all the required params for the activation email
    through celery task
    """
    if user_registration is None:
        user_registration = Registration.objects.get(user=user)

    message_context = generate_activation_email_context(user, user_registration)
    message_context.update({
        'confirm_activation_link': _get_activation_confirmation_link(message_context['key'], redirect_url),
        'route_enabled': route_enabled,
        'routed_user': user.username,
        'routed_user_email': user.email,
        'routed_profile_name': profile_name,
    })

    if route_enabled:
        dest_addr = settings.FEATURES['REROUTE_ACTIVATION_EMAIL']
    else:
        dest_addr = user.email

    msg = AccountActivation().personalize(
        recipient=Recipient(user.id, dest_addr),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=message_context,
    )

    return msg


def _get_activation_confirmation_link(activation_key, redirect_url=None):
    """
    Helper function to build an activation confirmation URL given an activation_key.
    The confirmation URL will include a "?next={redirect_url}" query if redirect_url
    is not null.
    """
    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    confirmation_link = '{root_url}/activate/{activation_key}'.format(
        root_url=root_url,
        activation_key=activation_key,
    )
    if not redirect_url:
        return confirmation_link

    scheme, netloc, path, params, _, fragment = urllib.parse.urlparse(confirmation_link)
    query = urllib.parse.urlencode({'next': redirect_url})
    return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))


def compose_and_send_activation_email(user, profile, user_registration=None, redirect_url=None):
    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        profile: profile object of the current logged-in user
        user_registration: registration of the current logged-in user
        redirect_url: The URL to redirect to after successful activation
    """
    route_enabled = settings.FEATURES.get('REROUTE_ACTIVATION_EMAIL')

    msg = compose_activation_email(user, user_registration, route_enabled, profile.name, redirect_url)
    from_address = configuration_helpers.get_value('ACTIVATION_EMAIL_FROM_ADDRESS') or (
        configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    )

    try:
        send_activation_email.delay(str(msg), from_address)
    except Exception:  # pylint: disable=broad-except
        log.exception(f'Activation email task failed for user {user.id}.')


@login_required
def course_run_refund_status(request, course_id):
    """
    Get Refundable status for a course.

    Arguments:
        request: The request object.
        course_id (str): The unique identifier for the course.

    Returns:
        Json response.

    """

    try:
        course_key = CourseKey.from_string(course_id)
        course_enrollment = CourseEnrollment.get_enrollment(request.user, course_key)

    except InvalidKeyError:
        logging.exception("The course key used to get refund status caused InvalidKeyError during look up.")

        return JsonResponse({'course_refundable_status': ''}, status=406)

    refundable_status = course_enrollment.refundable()
    logging.info(f"Course refund status for course {course_id} is {refundable_status}")

    return JsonResponse({'course_refundable_status': refundable_status}, status=200)


def _update_email_opt_in(request, org):
    """
    Helper function used to hit the profile API if email opt-in is enabled.
    """

    email_opt_in = request.POST.get('email_opt_in')
    if email_opt_in is not None:
        email_opt_in_boolean = email_opt_in == 'true'
        preferences_api.update_email_opt_in(request.user, org, email_opt_in_boolean)


@transaction.non_atomic_requests
@require_POST
@outer_atomic()
def change_enrollment(request, check_access=True):
    """
    Modify the enrollment status for the logged-in user.

    TODO: This is lms specific and does not belong in common code.

    The request parameter must be a POST request (other methods return 405)
    that specifies course_id and enrollment_action parameters. If course_id or
    enrollment_action is not specified, if course_id is not valid, if
    enrollment_action is something other than "enroll" or "unenroll", if
    enrollment_action is "enroll" and enrollment is closed for the course, or
    if enrollment_action is "unenroll" and the user is not enrolled in the
    course, a 400 error will be returned. If the user is not logged in, 403
    will be returned; it is important that only this case return 403 so the
    front end can redirect the user to a registration or login page when this
    happens. This function should only be called from an AJAX request, so
    the error messages in the responses should never actually be user-visible.

    Args:
        request (`Request`): The Django request object

    Keyword Args:
        check_access (boolean): If True, we check that an accessible course actually
            exists for the given course_key before we enroll the student.
            The default is set to False to avoid breaking legacy code or
            code with non-standard flows (ex. beta tester invitations), but
            for any standard enrollment flow you probably want this to be True.

    Returns:
        Response

    """
    # Get the user
    user = request.user

    # Ensure the user is authenticated
    if not user.is_authenticated:
        return HttpResponseForbidden()

    # Ensure we received a course_id
    action = request.POST.get("enrollment_action")
    if 'course_id' not in request.POST:
        return HttpResponseBadRequest(_("Course id not specified"))

    try:
        course_id = CourseKey.from_string(request.POST.get("course_id"))
    except InvalidKeyError:
        log.warning(
            "User %s tried to %s with invalid course id: %s",
            user.username,
            action,
            request.POST.get("course_id"),
        )
        return HttpResponseBadRequest(_("Invalid course id"))

    # Allow us to monitor performance of this transaction on a per-course basis since we often roll-out features
    # on a per-course basis.
    monitoring_utils.set_custom_attribute('course_id', str(course_id))

    if action == "enroll":
        # Make sure the course exists
        # We don't do this check on unenroll, or a bad course id can't be unenrolled from
        if not modulestore().has_course(course_id):
            log.warning(
                "User %s tried to enroll in non-existent course %s",
                user.username,
                course_id
            )
            return HttpResponseBadRequest(_("Course id is invalid"))

        # Record the user's email opt-in preference
        if settings.FEATURES.get('ENABLE_MKTG_EMAIL_OPT_IN'):
            _update_email_opt_in(request, course_id.org)

        available_modes = CourseMode.modes_for_course_dict(course_id)

        # Check whether the user is blocked from enrolling in this course
        # This can occur if the user's IP is on a global blacklist
        # or if the user is enrolling in a country in which the course
        # is not available.
        redirect_url = embargo_api.redirect_if_blocked(request, course_id)
        if redirect_url:
            return HttpResponse(redirect_url)

        if CourseEntitlement.check_for_existing_entitlement_and_enroll(user=user, course_run_key=course_id):
            return HttpResponse(reverse('courseware', args=[str(course_id)]))

        # Check that auto enrollment is allowed for this course
        # (= the course is NOT behind a paywall)
        if CourseMode.can_auto_enroll(course_id):
            # Enroll the user using the default mode (audit)
            # We're assuming that users of the course enrollment table
            # will NOT try to look up the course enrollment model
            # by its slug.  If they do, it's possible (based on the state of the database)
            # for no such model to exist, even though we've set the enrollment type
            # to "audit".
            try:
                enroll_mode = CourseMode.auto_enroll_mode(course_id, available_modes)
                if enroll_mode:
                    CourseEnrollment.enroll(user, course_id, check_access=check_access, mode=enroll_mode)
            except Exception:  # pylint: disable=broad-except
                return HttpResponseBadRequest(_("Could not enroll"))

        # If we have more than one course mode or professional ed is enabled,
        # then send the user to the choose your track page.
        # (In the case of no-id-professional/professional ed, this will redirect to a page that
        # funnels users directly into the verification / payment flow)
        if CourseMode.has_verified_mode(available_modes) or CourseMode.has_professional_mode(available_modes):
            return HttpResponse(
                reverse("course_modes_choose", kwargs={'course_id': str(course_id)})
            )

        # Otherwise, there is only one mode available (the default)
        return HttpResponse()
    elif action == "unenroll":
        if configuration_helpers.get_value(
            "DISABLE_UNENROLLMENT",
            settings.FEATURES.get("DISABLE_UNENROLLMENT")
        ):
            return HttpResponseBadRequest(_("Unenrollment is currently disabled"))

        enrollment = CourseEnrollment.get_enrollment(user, course_id)
        if not enrollment:
            return HttpResponseBadRequest(_("You are not enrolled in this course"))

        certificate_info = cert_info(user, enrollment)
        if certificate_info.get('status') in DISABLE_UNENROLL_CERT_STATES:
            return HttpResponseBadRequest(_("Your certificate prevents you from unenrolling from this course"))

        try:
            CourseEnrollment.unenroll(user, course_id)
        except UnenrollmentNotAllowed as exc:
            return HttpResponseBadRequest(str(exc))

        REFUND_ORDER.send(sender=None, course_enrollment=enrollment)
        return HttpResponse()
    else:
        return HttpResponseBadRequest(_("Enrollment action is invalid"))


@require_GET
@login_required
@ensure_csrf_cookie
def manage_user_standing(request):
    """
    Renders the view used to manage user standing. Also displays a table
    of user accounts that have been disabled and who disabled them.
    """
    if not request.user.is_staff:
        raise Http404
    all_disabled_accounts = UserStanding.objects.filter(
        account_status=UserStanding.ACCOUNT_DISABLED
    )

    all_disabled_users = [standing.user for standing in all_disabled_accounts]

    headers = ['username', 'account_changed_by']
    rows = []
    for user in all_disabled_users:
        row = [user.username, user.standing.changed_by]
        rows.append(row)

    context = {'headers': headers, 'rows': rows}

    return render_to_response("manage_user_standing.html", context)


@require_POST
@login_required
@ensure_csrf_cookie
def disable_account_ajax(request):
    """
    Ajax call to change user standing. Endpoint of the form
    in manage_user_standing.html
    """
    if not request.user.is_staff:
        raise Http404
    username = request.POST.get('username')
    context = {}
    if username is None or username.strip() == '':
        context['message'] = _('Please enter a username')
        return JsonResponse(context, status=400)

    account_action = request.POST.get('account_action')
    if account_action is None:
        context['message'] = _('Please choose an option')
        return JsonResponse(context, status=400)

    username = username.strip()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        context['message'] = _("User with username {} does not exist").format(username)
        return JsonResponse(context, status=400)
    else:
        user_account, _success = UserStanding.objects.get_or_create(
            user=user, defaults={'changed_by': request.user},
        )
        if account_action == 'disable':
            user_account.account_status = UserStanding.ACCOUNT_DISABLED
            context['message'] = _("Successfully disabled {}'s account").format(username)
            log.info("%s disabled %s's account", request.user, username)
        elif account_action == 'reenable':
            user_account.account_status = UserStanding.ACCOUNT_ENABLED
            context['message'] = _("Successfully reenabled {}'s account").format(username)
            log.info("%s reenabled %s's account", request.user, username)
        else:
            context['message'] = _("Unexpected account status")
            return JsonResponse(context, status=400)
        user_account.changed_by = request.user
        user_account.standing_last_changed_at = datetime.datetime.now(UTC)
        user_account.save()

    return JsonResponse(context)


@receiver(post_save, sender=User)
def user_signup_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handler that saves the user Signup Source when the user is created
    """
    if 'created' in kwargs and kwargs['created']:
        site = configuration_helpers.get_value('SITE_NAME')
        if site:
            user_signup_source = UserSignupSource(user=kwargs['instance'], site=site)
            user_signup_source.save()
            log.info('user {} originated from a white labeled "Microsite"'.format(kwargs['instance'].id))


@ensure_csrf_cookie
def activate_account(request, key):
    """
    When link in activation e-mail is clicked
    """
    # If request is in Studio call the appropriate view
    if theming_helpers.get_project_root_name().lower() == 'cms':
        monitoring_utils.set_custom_attribute('student_activate_account', 'cms')
        return activate_account_studio(request, key)

    # TODO: Use custom attribute to determine if there are any `activate_account` calls for cms in Production.
    # If not, the templates wouldn't be needed for cms, but we still need a way to activate for cms tests.
    monitoring_utils.set_custom_attribute('student_activate_account', 'lms')
    activation_message_type = None

    activated_or_confirmed = 'confirmed' if settings.MARKETING_EMAILS_OPT_IN else 'activated'
    account_or_email = 'email' if settings.MARKETING_EMAILS_OPT_IN else 'account'

    invalid_message = HTML(_(
        '{html_start}Your {account_or_email} could not be {activated_or_confirmed}{html_end}'
        'Something went wrong, please <a href="{support_url}">contact support</a> to resolve this issue.'
    )).format(
        account_or_email=account_or_email,
        activated_or_confirmed=activated_or_confirmed,
        support_url=configuration_helpers.get_value(
            'ACTIVATION_EMAIL_SUPPORT_LINK', settings.ACTIVATION_EMAIL_SUPPORT_LINK
        ) or settings.SUPPORT_SITE_LINK,
        html_start=HTML('<p class="message-title">'),
        html_end=HTML('</p>'),
    )

    show_account_activation_popup = None
    try:
        registration = Registration.objects.get(activation_key=key)
    except (Registration.DoesNotExist, Registration.MultipleObjectsReturned):
        activation_message_type = 'error'
        messages.error(
            request,
            invalid_message,
            extra_tags='account-activation aa-icon'
        )
    else:
        if request.user.is_authenticated and request.user.id != registration.user.id:
            activation_message_type = 'error'
            messages.error(
                request,
                invalid_message,
                extra_tags='account-activation aa-icon'
            )
        elif registration.user.is_active:
            activation_message_type = 'info'
            messages.info(
                request,
                HTML(_(
                    '{html_start}This {account_or_email} has already been {activated_or_confirmed}.{html_end}'
                )).format(
                    account_or_email=account_or_email,
                    activated_or_confirmed=activated_or_confirmed,
                    html_start=HTML('<p class="message-title">'),
                    html_end=HTML('</p>'),
                ),
                extra_tags='account-activation aa-icon',
            )
        else:
            registration.activate()
            # Success message for logged in users.
            message = _('{html_start}Success{html_end} You have {activated_or_confirmed} your {account_or_email}.')

            tracker.emit(
                USER_ACCOUNT_ACTIVATED,
                {
                    "user_id": registration.user.id,
                    "activation_timestamp": registration.activation_timestamp
                }
            )

            if not request.user.is_authenticated:
                # Success message for logged out users
                message = _(
                    '{html_start}Success! You have {activated_or_confirmed} your {account_or_email}.{html_end}'
                    'You will now receive email updates and alerts from us related to'
                    ' the courses you are enrolled in. Sign In to continue.'
                )

            # Add message for later use.
            activation_message_type = 'success'
            messages.success(
                request,
                HTML(message).format(
                    account_or_email=account_or_email,
                    activated_or_confirmed=activated_or_confirmed,
                    html_start=HTML('<p class="message-title">'),
                    html_end=HTML('</p>'),
                ),
                extra_tags='account-activation aa-icon',
            )
            show_account_activation_popup = request.COOKIES.get(settings.SHOW_ACTIVATE_CTA_POPUP_COOKIE_NAME, None)

    # If a safe `next` parameter is provided in the request
    # and it's not the same as the dashboard, redirect there.
    # The `get_next_url_for_login_page()` function will only return a safe redirect URL.
    # If the provided `next` URL is not safe, that function will fill `redirect_to`
    # with a value of `reverse('dashboard')`.
    redirect_url = None
    if request.GET.get('next'):
        redirect_to, root_login_url = get_next_url_for_login_page(request, include_host=True)

        # Don't automatically redirect authenticated users to the redirect_url
        # if the `next` value is either:
        # 1. "/dashboard" or
        # 2. "https://{LMS_ROOT_URL}/dashboard" (which we might provide as a value from the AuthN MFE)
        if redirect_to not in (
            root_login_url + reverse('dashboard'),
            reverse('dashboard')
        ):
            redirect_url = get_redirect_url_with_host(root_login_url, redirect_to)

    if should_redirect_to_authn_microfrontend() and not request.user.is_authenticated:
        params = {'account_activation_status': activation_message_type}
        if redirect_url:
            params['next'] = redirect_url
        url_path = '/login?{}'.format(urllib.parse.urlencode(params))
        return redirect(settings.AUTHN_MICROFRONTEND_URL + url_path)

    response = redirect(redirect_url) if redirect_url and is_enterprise_learner(request.user) else redirect('dashboard')
    if show_account_activation_popup:
        response.delete_cookie(
            settings.SHOW_ACTIVATE_CTA_POPUP_COOKIE_NAME,
            domain=settings.SESSION_COOKIE_DOMAIN,
            path='/',
        )
    return response


@ensure_csrf_cookie
def activate_account_studio(request, key):
    """
    When link in activation e-mail is clicked and the link belongs to studio.
    """
    try:
        registration = Registration.objects.get(activation_key=key)
    except (Registration.DoesNotExist, Registration.MultipleObjectsReturned):
        return render_to_response(
            "registration/activation_invalid.html",
            {'csrf': csrf(request)['csrf_token']}
        )
    else:
        user_logged_in = request.user.is_authenticated
        already_active = True
        if not registration.user.is_active:
            registration.activate()
            already_active = False

        return render_to_response(
            "registration/activation_complete.html",
            {
                'user_logged_in': user_logged_in,
                'already_active': already_active
            }
        )


def validate_new_email(user, new_email):
    """
    Given a new email for a user, does some basic verification of the new address If any issues are encountered
    with verification a ValueError will be thrown.
    """
    try:
        validate_email(new_email)
    except ValidationError:
        raise ValueError(_('Valid e-mail address required.'))  # lint-amnesty, pylint: disable=raise-missing-from

    if new_email == user.email:
        raise ValueError(_('Old email is the same as the new email.'))


def validate_secondary_email(user, new_email):
    """
    Enforce valid email addresses.
    """

    from openedx.core.djangoapps.user_api.accounts.api import get_email_validation_error, \
        get_secondary_email_validation_error

    if get_email_validation_error(new_email):
        raise ValueError(_('Valid e-mail address required.'))

    # Make sure that if there is an active recovery email address, that is not the same as the new one.
    if hasattr(user, "account_recovery"):
        if user.account_recovery.is_active and new_email == user.account_recovery.secondary_email:
            raise ValueError(_('Old email is the same as the new email.'))

    # Make sure that secondary email address is not same as user's primary email.
    if new_email == user.email:
        raise ValueError(_('Cannot be same as your sign in email address.'))

    message = get_secondary_email_validation_error(new_email)
    if message:
        raise ValueError(message)


def do_email_change_request(user, new_email, activation_key=None, secondary_email_change_request=False):
    """
    Given a new email for a user, does some basic verification of the new address and sends an activation message
    to the new address. If any issues are encountered with verification or sending the message, a ValueError will
    be thrown.
    """
    # if activation_key is not passing as an argument, generate a random key
    if not activation_key:
        activation_key = uuid.uuid4().hex

    confirm_link = reverse('confirm_email_change', kwargs={'key': activation_key, })

    if secondary_email_change_request:
        PendingSecondaryEmailChange.objects.update_or_create(
            user=user,
            defaults={
                'new_secondary_email': new_email,
                'activation_key': activation_key,
            }
        )
        confirm_link = reverse('activate_secondary_email', kwargs={'key': activation_key})
    else:
        PendingEmailChange.objects.update_or_create(
            user=user,
            defaults={
                'new_email': new_email,
                'activation_key': activation_key,
            }
        )

    use_https = theming_helpers.get_current_request().is_secure()

    site = Site.objects.get_current()
    message_context = get_base_template_context(site)
    message_context.update({
        'old_email': user.email,
        'new_email': new_email,
        'confirm_link': '{protocol}://{site}{link}'.format(
            protocol='https' if use_https else 'http',
            site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
            link=confirm_link,
        ),
    })

    if secondary_email_change_request:
        msg = RecoveryEmailCreate().personalize(
            recipient=Recipient(user.id, new_email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )
    else:
        msg = EmailChange().personalize(
            recipient=Recipient(user.id, new_email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )

    try:
        ace.send(msg)
        log.info("Email activation link sent to user [%s].", new_email)
    except Exception:
        from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        log.error('Unable to send email activation link to user from "%s"', from_address, exc_info=True)
        raise ValueError(_('Unable to send email activation link. Please try again later.'))  # lint-amnesty, pylint: disable=raise-missing-from

    if not secondary_email_change_request:
        # When the email address change is complete, a "edx.user.settings.changed" event will be emitted.
        # But because changing the email address is multi-step, we also emit an event here so that we can
        # track where the request was initiated.
        tracker.emit(
            SETTING_CHANGE_INITIATED,
            {
                "setting": "email",
                "old": message_context['old_email'],
                "new": message_context['new_email'],
                "user_id": user.id,
            }
        )


@ensure_csrf_cookie
def activate_secondary_email(request, key):
    """
    This is called when the activation link is clicked. We activate the secondary email
    for the requested user.
    """
    try:
        pending_secondary_email_change = PendingSecondaryEmailChange.objects.get(activation_key=key)
    except PendingSecondaryEmailChange.DoesNotExist:
        return render_to_response("invalid_email_key.html", {})

    try:
        account_recovery = pending_secondary_email_change.user.account_recovery
    except AccountRecovery.DoesNotExist:
        account_recovery = AccountRecovery(user=pending_secondary_email_change.user)

    try:
        account_recovery.update_recovery_email(pending_secondary_email_change.new_secondary_email)
    except ValidationError:
        return render_to_response("secondary_email_change_failed.html", {
            'secondary_email': pending_secondary_email_change.new_secondary_email
        })

    pending_secondary_email_change.delete()

    return render_to_response("secondary_email_change_successful.html")


@ensure_csrf_cookie
def confirm_email_change(request, key):
    """
    User requested a new e-mail. This is called when the activation
    link is clicked. We confirm with the old e-mail, and update
    """
    with transaction.atomic():
        try:
            pec = PendingEmailChange.objects.get(activation_key=key)
        except PendingEmailChange.DoesNotExist:
            response = render_to_response("invalid_email_key.html", {})
            transaction.set_rollback(True)
            return response

        user = pec.user
        address_context = {
            'old_email': user.email,
            'new_email': pec.new_email
        }

        if len(User.objects.filter(email=pec.new_email)) != 0:
            response = render_to_response("email_exists.html", {})
            transaction.set_rollback(True)
            return response

        use_https = request.is_secure()
        if settings.FEATURES['ENABLE_MKTG_SITE']:
            contact_link = marketing_link('CONTACT')
        else:
            contact_link = '{protocol}://{site}{link}'.format(
                protocol='https' if use_https else 'http',
                site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
                link=reverse('contact'),
            )

        site = Site.objects.get_current()
        message_context = get_base_template_context(site)
        message_context.update({
            'old_email': user.email,
            'new_email': pec.new_email,
            'contact_link': contact_link,
            'from_address': configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
        })

        msg = EmailChangeConfirmation().personalize(
            recipient=Recipient(user.id, user.email),
            language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
            user_context=message_context,
        )

        u_prof = UserProfile.objects.get(user=user)
        meta = u_prof.get_meta()
        if 'old_emails' not in meta:
            meta['old_emails'] = []
        meta['old_emails'].append([user.email, datetime.datetime.now(UTC).isoformat()])
        u_prof.set_meta(meta)
        u_prof.save()
        # Send it to the old email...
        try:
            ace.send(msg)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to old address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': user.email})
            transaction.set_rollback(True)
            return response

        user.email = pec.new_email
        user.save()
        pec.delete()
        # And send it to the new email...
        msg.recipient = Recipient(user.id, pec.new_email)
        try:
            ace.send(msg)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send confirmation email to new address', exc_info=True)
            response = render_to_response("email_change_failed.html", {'email': pec.new_email})
            transaction.set_rollback(True)
            return response

        response = render_to_response("email_change_successful.html", address_context)

        USER_EMAIL_CHANGED.send(sender=None, user=user)
        return response


@api_view(['POST'])
@authentication_classes((
    JwtAuthentication,
    BearerAuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
))
@permission_classes((IsAuthenticated,))
def change_email_settings(request):
    """
    Modify logged-in user's setting for receiving emails from a course.
    """
    user = request.user

    course_id = request.data.get("course_id")
    receive_emails = request.data.get("receive_emails")
    course_key = CourseKey.from_string(course_id)

    if receive_emails:
        optout_object = Optout.objects.filter(user=user, course_id=course_key)
        if optout_object:
            optout_object.delete()
        log.info(
            "User %s (%s) opted in to receive emails from course %s",
            user.username,
            user.email,
            course_id,
        )
        track_views.server_track(
            request,
            "change-email-settings",
            {"receive_emails": "yes", "course": course_id},
            page='dashboard',
        )
    else:
        Optout.objects.get_or_create(user=user, course_id=course_key)
        log.info(
            "User %s (%s) opted out of receiving emails from course %s",
            user.username,
            user.email,
            course_id,
        )
        track_views.server_track(
            request,
            "change-email-settings",
            {"receive_emails": "no", "course": course_id},
            page='dashboard',
        )

    return JsonResponse({"success": True})


@csrf_exempt
def extras_course_enroll_user(request):

    data = json.loads(request.body)
    log.info(data)

    try:
        username = data["other"]["username"]
        first_name = data["other"]["first_name"]
        last_name = data["other"]["last_name"]
        email = data["other"]["email"]
        password = data["other"]["password"]  
        unenroll = data["other"]["unenroll"]
	 
    except MultiValueDictKeyError:
        return render(request, 'blank.html', {"message": "Invalid Options"})

    username = username.replace(".", "_")
    username = username.replace(" ", "_")

    if (len(username) > 30):
        username = username[0:30]

    try:
        user = User.objects.get(email = email)
    except ObjectDoesNotExist:
        user = _create_user(username, email, first_name, last_name, password)

    if "site_id" in data["other"]:
        if data["other"]["site_id"] == "DLT":
            _create_soical_auth_record(email, "azuread-oauth2")
        elif data["other"]["site_id"] in ["GIAP", "eMBA"]:
            _create_soical_auth_record(email, "google-oauth2")
    
    context = {"message" : "Registered User %s" %(email)}

    if "course_number_run" in data["other"]:
        course = data['other']['course_number_run'].split("|")[0]
        run = data['other']['course_number_run'].split("|")[1]
        org = data['other']["site_id"]

        course_id = "course-v1:{0}+{1}+{2}".format(org, course, run)

        user = User.objects.get(email = email)

        if unenroll:
            _extras_deactivate_enrollments(user, course_id)
            context = {"message": "Removed user %s from course %s"%(user, course_id)}
        else:
            add_enrollment(user, course_id)
            context = {"message": "Added user %s to course %s"%(user, course_id)}
         
    log.error(context)
    return render(request, "blank.html", context)


def _create_soical_auth_record(user_email, provider_name):
    user = User.objects.get(email = user_email)
    try:
        record = UserSocialAuth.objects.filter(user = user, provider = provider_name)
        if not record:
            UserSocialAuth.objects.create(
                    user = user,
                    uid = user.email,
                    provider = provider_name
                    )
            log.info("Created social auth record for %s "%(user))
        else:
            log.error("Social auth record already exists for user %s"%(user))
    except Exception as err:
        log.error("Exception occured while creating social auth record. Error Details: %s"%(str(err)))



def _create_user(username, email, first_name, last_name, password):

    f = AccountCreationForm(
        data={
            'username': username,
            'email': email,
            'password': password,
            'name': first_name + " " + last_name

        },
        tos_required=False
    )

    (user, _, _) = do_create_account(f)
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True
    user.save()



def _extras_deactivate_enrollments(user, ckey = None):
    if ckey != None:
        es = CourseEnrollment.objects.filter(user = user).filter(course_id = CourseKey.from_string(ckey))
    else:
        es = CourseEnrollment.objects.filter(user = user)

    for e in es:
        e.is_active = False
        e.save()


def _get_delimiter(index):
	try:
		unicodes = [u'\u2016', u'\u2191', u'\u2193', u'\u219f', u'\u21c8', u'\u21ca', u'\u21e1', u'\u21a5', u'\u21e3', u'\u21be'] 
		return unicodes[index]	
	except Exception as err:
		log.error("Zoom unicode error : " + str(err))
		return "|"

def _get_zoom_auth_token():
    session_key = "zoom-auth-token" + configuration_helpers.get_value("ZOOM_ACCOUNT_ID", "mRKuJqD7TgWa6Avp6E9v9Q")
    if cache.get(session_key, ""):
        return cache.get(session_key, "")

    zoom_oauth_url = "https://zoom.us/oauth/token"
    zoom_token = configuration_helpers.get_value("ZOOM_API_KEY", "")
    data={'grant_type': 'account_credentials', 'account_id': configuration_helpers.get_value("ZOOM_ACCOUNT_ID", "mRKuJqD7TgWa6Avp6E9v9Q")}
    response = requests.post(zoom_oauth_url, data=data, headers={"Authorization" : zoom_token})
    log.info(response.text)
    r_data = json.loads(response.text)
    if response.status_code != 200:
        return ""

    cache.set(session_key, "{0} {1}".format(r_data["token_type"], r_data["access_token"]), 3300)
    return cache.get(session_key, "")

def get_zoom_link(meeting_id, webinar_id, data):
    user = User.objects.get(email = data["email"]) 
    session_key = str(meeting_id) + "-" + str(user.id)
    MEMCACHE_TIMEOUT = 28800
    join_url = cache.get(session_key, None)
    space_unicode = u'\u0020'
    r_data = {}
    if join_url is not None:
        log.info("Key exists in the session")
        r_data["join_url"] = join_url
    else:
        log.info("Registering user in zoom " + data["email"])
        zoom_data = {"email" : data["email"]}
        if meeting_id != "0":
            delimiter = _get_delimiter(int(meeting_id[-1]))
            zoom_url = "https://api.zoom.us/v2/meetings/" + meeting_id +"/registrants"
        elif webinar_id != "0":
            delimiter = _get_delimiter(int(webinar_id[-1]))
            zoom_url = "https://api.zoom.us/v2/webinars/" + webinar_id +"/registrants"
        if "@talentsprint.com" in data["email"]:
            first_name = data["first_name"] + " " + delimiter + space_unicode
            last_name = "TS"
        elif "@email.iimcal.ac.in" in data["email"] or data["username"].startswith("dp-"):
            first_name = data["first_name"] + " " + delimiter + " "
            if "-" in data["username"]:
                last_name = "-".join(data["username"].split("-")[1:]) 
            else:
                last_name = data["username"]
        elif "@iimcal.ac.in" in data["email"]:
            full_name = data["first_name"] + " " + data["last_name"] 
            first_name = full_name + " " + delimiter + " "
            last_name = "IIM Calcutta" 
            
        elif "@iitjammu.ac.in" in data["email"] and data["username"].startswith("20"):
            full_name =  data["first_name"] + " " + data["last_name"]
            first_name = full_name + " " + delimiter + " "
            last_name = data["username"]
        else:
            if data["last_name"]:
                first_name = data["first_name"] + " " + delimiter + " "
                last_name = data["last_name"]
            else:
                first_name = data["first_name"]
                last_name = "|"
        zoom_data = {"email" : data["email"], "first_name" : first_name, "last_name" : last_name}
        log.error(zoom_data)
        
        zoom_token = _get_zoom_auth_token()
        if zoom_token:
            headers = {"Authorization" : zoom_token, "Content-Type" : "application/json"}
            response = requests.post(zoom_url, data=json.dumps(zoom_data), headers=headers)
            log.info(response.text)
            r_data = json.loads(response.text)
            if "join_url" in r_data:
                cache.set(session_key, r_data["join_url"], MEMCACHE_TIMEOUT) 
    return r_data

@csrf_exempt
@login_required
def extras_join_zoom(request, course_id):
	try:
		course_key = CourseKey.from_string(course_id)
		cdn_data = {"org" : [str(course_key.org)], "course_id" : course_id}
		r = requests.post("https://cdn.exec.talentsprint.com/app/getMeetingRooms", headers = {'content-type': 'application/json'}, data = json.dumps(cdn_data))
		r_data = json.loads(r.text)
		log.error(r_data)
		meeting_id = r_data["meeting_id"]
		data = {"email" : request.user.email, "username" : request.user.username, "first_name" : request.user.first_name, "last_name" : request.user.last_name}
		zoom_data = get_zoom_link(meeting_id, "0", data)
		log.error(zoom_data)
		return redirect(zoom_data["join_url"])
	except Exception as err:
		log.error("ZOOM Error: " + str(err))
		return HttpResponse("Please contact support")


@login_required
def join_zoom_meeting(request):
	try:
		meeting_id = request.GET["meeting_id"]
		data = {"email" : request.user.email, "username" : request.user.username, "first_name" : request.user.first_name, "last_name" : request.user.last_name} 

		r_data = get_zoom_link(meeting_id, "0", data)
		log.error(r_data)
		return redirect(r_data["join_url"])
	except Exception as err:
		log.error("ZOOM Error: " + str(err))
		return HttpResponse("Please contact support")


@xframe_options_exempt
@csrf_exempt
@login_required
def  extras_get_moodle_grades(request):
        user_email = request.user.email
        multiple_moodle = configuration_helpers.get_value("MULTIPLE_MOODLE", False)
        if multiple_moodle:
            moodle_base_url = configuration_helpers.get_value("MULTIPLE_MOODLE_URLS","")
        else:
            moodle_base_url = [configuration_helpers.get_value("MOODLE_URL", "")]

        moodle_wstoken = configuration_helpers.get_value("MOODLE_TOKEN", "")
        overall_scores_function = "gradereport_overview_get_course_grades"
        course_scores_function = "gradereport_user_get_grade_items"
        headers = {  'content-type': "text/plain" }
        #Fetch cumulative scores for all enrolled courses from moodle
        querystring = {"wstoken" : moodle_wstoken, "wsfunction" : overall_scores_function, "moodlewsrestformat" : "json", "user_email" : user_email, "site_name" : configuration_helpers.get_value("course_org_filter", "")}
        responses = {}
        for index_no , api_url in enumerate(moodle_base_url):
            moodle_service_url = api_url + "/webservice/rest/server.php"
            response = requests.request("POST", moodle_service_url, headers = headers, params = querystring)

            log.info("API call response for Course {0} url is {1} ".format(api_url, response.status_code))

            context = json.loads(response.text)
            if "message" in context or not context["grades"]:
                continue
            grades_querystring = {"wstoken" : moodle_wstoken, "wsfunction" : course_scores_function, "moodlewsrestformat" : "json", "user_email" : user_email, "site_name" : configuration_helpers.get_value("course_org_filter", ""), "custom_request" : "Gradebook", "courseid" : 0}
            grades_response = requests.request("POST", moodle_service_url, headers = headers, params = grades_querystring)
            log.info("API call response for Grades {0} url is {1}".format(api_url, response.status_code))

            data = json.loads(grades_response.text)
            for i in range(len(context["grades"])):
                for grades in data["usergrades"]:
                    if grades["gradeitems"]:
                        if context["grades"][i]["courseid"] == grades["courseid"]:
                            context["grades"][i]["individual_scores"] = grades["gradeitems"]
                            break

                    else:
                        context["grades"][i]["individual_scores"] = []

            if "Response" + str(index_no) not in responses:
                responses["Response" + str(index_no)] = context

        final_response = merge_grades(responses) if len(responses) > 1 else responses.get(list(responses.keys())[0]) if len(responses) == 1 else {}
        final_response.update({"studentid" : request.user.last_name, "studentname" : request.user.first_name})

        if configuration_helpers.get_value('EXTRAS_GRADES_MOODLE_GRADEBOOK_TEMPLATE'):
            return render(request, configuration_helpers.get_value('EXTRAS_GRADES_MOODLE_GRADEBOOK_TEMPLATE'), context = final_response)
        else:
            return render(request, "gradebook.html", context = final_response)



def merge_grades(responses):
    mergeddata = {}
    for key,value in responses.items():
        for grade_keys, grade_report in value.items():
            if isinstance(grade_report, list):
                mergeddata[grade_keys] = grade_report if grade_keys not in mergeddata else mergeddata[grade_keys] + grade_report
                continue
            if grade_keys not in ["userid"]:
                mergeddata[grade_keys] = grade_report if grade_keys not in mergeddata else float(mergeddata[grade_keys]) + float(grade_report)


    mergeddata["total_submissions_in_percentage"] = 0 if mergeddata["total_submissions"] == 0 else (mergeddata["user_submissions"] / mergeddata["total_submissions"]) * 100 
    mergeddata["overall_percentage"] = 0 if mergeddata["total_scores"] == 0 else (mergeddata["user_scores"] / mergeddata["total_scores"]) * 100
    return mergeddata


@login_required
def attendance_report(request):
    try:
        moodle_base_url = configuration_helpers.get_value("MOODLE_URL", "")
        moodle_service_url = moodle_base_url + "/webservice/rest/server.php"
        moodle_wstoken = configuration_helpers.get_value("MOODLE_TOKEN", "")
        course_attendance_function = "mod_wsattendance_get_attendance"
        if "site" in request.GET:
            site = request.GET["site"]
        else:
            site = ""
        headers = {'content-type': "text/plain"}
        querystring = {"wstoken" : moodle_wstoken, "wsfunction" : course_attendance_function, "moodlewsrestformat" : "json", "user_email":request.user.email, "site_name" :  site }
        response = requests.request("POST", moodle_service_url, headers = headers, params = querystring)
        context = {'attendance_report' : json.loads(response.text), 'cohort_name' : request.GET["cohort_name"]}
        if configuration_helpers.get_value('ATTENDANCE_TEMPLATE'):
            return render(request, configuration_helpers.get_value('ATTENDANCE_TEMPLATE'), context = context)
        else :
            return render(request, 'attendance_report.html', context = context)
    except Exception as e:
        log.info(e)
        return {}


@csrf_exempt
def extras_reset_password_link(request):
	email = request.POST.get("email")
	domain = request.POST.get("domain")
	try:
            user = User.objects.get(email__iexact=email.strip())
	except Exception as err:
            log.error("Reset Password Error: "+ str(err) + " Email:" + email)
            return HttpResponse("")
	uid = int_to_base36(user.id)
	token = PasswordResetTokenGenerator().make_token(user)
	url = "https://{0}/password_reset_confirm/{1}-{2}".format(domain, uid, token)
	return HttpResponse(url)


@login_required
def user_tracker_link(request):
    params = {"wstoken": configuration_helpers.get_value("MOODLE_TOKEN", True), "wsfunction": "mod_assign_get_assignment_details", "moodlewsrestformat" : "json", "email": request.user.email, "site": configuration_helpers.get_value("course_org_filter", True)}
    data = requests.post(configuration_helpers.get_value("MOODLE_URL", "") + "/webservice/rest/server.php", data=params).json() 
    if configuration_helpers.get_value("course_org_filter", True) != 'TECHWISE':
        data = map(ist_to_utc, data)
    return render(request, 'user_tracker_link.html', {'data': data, 'program_image_url': configuration_helpers.get_value("MKTG_URLS", True)["HEADER_LOGO"]})


def ist_to_utc(item):
    utc = pytz.timezone("UTC")
    for date in ["start_date", "due_date"]:
        if item[date] != 'Jan 01, 1970 05:30 AM':
            dateobj = datetime.datetime.strptime(item[date], "%b %d, %Y %I:%M %p")
            utc_dt = utc.localize(dateobj)
            local_dt = utc_dt.astimezone(pytz.timezone('Asia/Kolkata'))
            item[date] = local_dt.strftime("%b %d, %Y %I:%M %p")
        else:
            item[date] = '-'
    return item


@csrf_exempt
def extras_get_user_enrolled_courses(request):
    user_email = request.POST.get("user_email")
    context = {}
    try:
        user = User.objects.get(email = user_email)
        user_courses = _get_active_inactive_courses(user)
        context['user_courses'] = user_courses
        context['user_details'] = {"name" : user.first_name , "roll_no" : user.username}
    except User.DoesNotExist:
        context['message'] = _("User with user email {} does not exist").format(user_email)
        return JsonResponse(context, status=400)
    return JsonResponse(context)

def _get_active_inactive_courses(user):
    user_courses = get_course_enrollments(user.username, include_inactive = True)
    user_active_inactive_courses = {}
    for i, user_course in enumerate(user_courses):
        if user_course["is_active"]:
            user_active_inactive_courses.update({user_course["course_details"]["course_id"] : "Active"})
        else:
            user_active_inactive_courses.update({user_course["course_details"]["course_id"] : "Dropped"})
    return user_active_inactive_courses

@csrf_exempt
def extras_get_last_login(request):
        secret_key = configuration_helpers.get_value("EXTRAS_USER_DETAILS_TOKEN", "MZi7J7jArBgY8YoSFfvrpIqH65LXIuNA")
        user_email = request.POST.get("email", "")
        token = request.POST.get("token", "")

        if secret_key != token:
                return JsonResponse({})
        if user_email == "" or user_email == None:
                return JsonResponse({"Error": "Enter a valid Email"})

        try:
                user = User.objects.get(email = user_email)
                return JsonResponse({"email": user.email, "username": user.username, "first_name": user.first_name, "last_name": user.last_name, "last_login": user.last_login})
        except Exception as e:
                log.info(e)
                return JsonResponse({"ERROR": "Something went wrong"})

            @login_required
def extras_start_mettl_test(request):
   test_id = request.GET["test_id"]
   HTTPVerb = "POST"
   URL = "https://api.mettl.com/v1/schedules/" + test_id + "/candidates"
   PUBLICKEY = configuration_helpers.get_value("METTL_PUBLIC_KEY", "95d3af46-0bd7-4610-a759-b46060e80760")
   PRIVATEKEY = configuration_helpers.get_value("METTL_PRIVATE_KEY", "beedfbbe-b1a8-47c7-aaa8-f11843d29393")
   registration_details = json.dumps({"registrationDetails":[{"Email Address" : request.user.email, "First Name" : request.user.username}]})
   timestamp = str(int(time.time()))
   message = HTTPVerb + URL + '\n' + PUBLICKEY + '\n' + registration_details + '\n' + timestamp
   sign = urllib.parse.quote(str(base64.b64encode(hmac.new(bytes(PRIVATEKEY, 'UTF-8') ,bytes(message, 'UTF-8') , digestmod=hashlib.sha1).digest()), "utf-8"))

   headers={"Content-Type" : "application/x-www-form-urlencoded"}
   payload = {"rd" : registration_details, "ak" : PUBLICKEY, "asgn" : sign, "ts" : timestamp}
   response = requests.post(URL, headers = headers, data = payload).json()
   log.error(payload)
   log.error(response)
   if response["status"] == "SUCCESS":
      if response["registrationStatus"][0]["url"] is not None:
           return redirect(response["registrationStatus"][0]["url"])
      elif response["registrationStatus"][0]["status"] == "Completed":
           return render(request, 'mettl_test_status.html', {"message" : "You have already completed your exam.Thank you!"})
      elif response["registrationStatus"][0]["status"] == "InValid":
           return render(request, 'mettl_test_status.html',{"message" : configuration_helpers.get_value("METTL_ERROR_MESSAGE", "You are not allowed to attend this exam owing to insufficient attendance. Please contact Support team")})

   return render(request, 'mettl_test_status.html', {"message" : "Uh ho! Something went wrong. Please contact support <br><a href=mailto:{0}>{0}</a>".format(configuration_helpers.get_value("contact_mailing_address", ""))})

@login_required
def extras_get_mettl_report(request):


    test_id = request.GET["test_id"]

    if test_id is None:
        return HttpResponse("Please contact Support")


    HTTPVerb = "GET"
    PUBLICKEY = configuration_helpers.get_value("METTL_PUBLIC_KEY", "95d3af46-0bd7-4610-a759-b46060e80760")
    PRIVATEKEY = configuration_helpers.get_value("METTL_PRIVATE_KEY", "beedfbbe-b1a8-47c7-aaa8-f11843d29393")
    URL = "https://api.mettl.com/v1/schedules/{0}/candidates/{1}".format(test_id, request.user.email)

    timestamp = str(int(time.time()))
    message = HTTPVerb + URL + '\n' + PUBLICKEY + '\n' + timestamp
    sign = str(base64.b64encode(hmac.new(bytes(PRIVATEKEY, 'UTF-8') ,bytes(message, 'UTF-8') , digestmod=hashlib.sha1).digest()), "utf-8")
    URL = "{url}?ak={access_key}&ts={timestamp}&asgn={sign}".format(url = URL, access_key = PUBLICKEY, timestamp = timestamp, sign = sign)

    response = requests.get(URL).json()

    log.info(response)

    if response["status"] != "SUCCESS" :
        return HttpResponse("Please Contact Support")

    return redirect(response["candidate"]["testStatus"]["htmlReport"])

@csrf_exempt
def extras_update_user_details(request):
        data = json.loads(request.body)
        log.info(data)
        try:
                oldEmail = data["other"]["email"]
                firstName = data["other"]["firstname"]
                lastName = data["other"]["lastname"]
                newEmail = data["other"]["newemail"]
                old_user = User.objects.get(email = oldEmail)

        except ObjectDoesNotExist:
                return HttpResponse("User doesn't exists")
        if newEmail and newEmail != oldEmail:
                try:
                        new_user = User.objects.get(email = newEmail)
                        if new_user:
                                return HttpResponse("User already exists with new email.")
                except ObjectDoesNotExist:
                        old_user.email = newEmail

        #update firstname lastname if email not passed
        if firstName is not None:
                old_user.first_name = firstName
        if lastName is not None:
                old_user.last_name = lastName
        old_user.save()
        return HttpResponse("Saved")