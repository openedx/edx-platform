"""
Views for login / logout and associated functionality

Much of this file was broken out from views.py, previous history can be found there.
"""

import datetime
import logging
import uuid
import warnings
from urlparse import parse_qs, urlsplit, urlunsplit

import analytics
import edx_oauth2_provider
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, load_backend, login as django_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.core.validators import ValidationError, validate_email
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.utils.http import base36_to_int, is_safe_url, urlencode, urlsafe_base64_encode
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from opaque_keys.edx.locator import CourseLocator
from provider.oauth2.models import Client
from ratelimitbackend.exceptions import RateLimitException
from requests import HTTPError
from six import text_type
from social_core.backends import oauth as social_oauth
from social_core.exceptions import AuthAlreadyAssociated, AuthException
from social_django import utils as social_utils

import openedx.core.djangoapps.external_auth.views
import third_party_auth
from django_comment_common.models import assign_role
from edxmako.shortcuts import render_to_response, render_to_string
from eventtracking import tracker
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.external_auth.login_and_register import login as external_auth_login
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.password_policy import compliance as password_policy_compliance
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.utils import generate_password
from openedx.core.djangoapps.util.user_messages import PageLevelMessages
from openedx.features.course_experience import course_home_url_name
from student.cookies import delete_logged_in_cookies, set_logged_in_cookies
from student.forms import AccountCreationForm
from student.helpers import (
    AccountValidationError,
    auth_pipeline_urls,
    create_or_set_user_attribute_created_on_site,
    generate_activation_email_context,
    get_next_url_for_login_page
)
from student.models import (
    CourseAccessRole,
    CourseEnrollment,
    LoginFailures,
    PasswordHistory,
    Registration,
    UserProfile,
    anonymous_id_for_user,
    create_comments_service_user
)
from student.helpers import authenticate_new_user, do_create_account
from third_party_auth import pipeline, provider
from util.json_request import JsonResponse

log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")


class AuthFailedError(Exception):
    """
    This is a helper for the login view, allowing the various sub-methods to early out with an appropriate failure
    message.
    """
    def __init__(self, value=None, redirect=None, redirect_url=None):
        self.value = value
        self.redirect = redirect
        self.redirect_url = redirect_url

    def get_response(self):
        resp = {'success': False}
        for attr in ('value', 'redirect', 'redirect_url'):
            if self.__getattribute__(attr) and len(self.__getattribute__(attr)):
                resp[attr] = self.__getattribute__(attr)

        return resp


def _do_third_party_auth(request):
    """
    User is already authenticated via 3rd party, now try to find and return their associated Django user.
    """
    running_pipeline = pipeline.get(request)
    username = running_pipeline['kwargs'].get('username')
    backend_name = running_pipeline['backend']
    third_party_uid = running_pipeline['kwargs']['uid']
    requested_provider = provider.Registry.get_from_pipeline(running_pipeline)
    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)

    try:
        return pipeline.get_authenticated_user(requested_provider, username, third_party_uid)
    except User.DoesNotExist:
        AUDIT_LOG.info(
            u"Login failed - user with username {username} has no social auth "
            "with backend_name {backend_name}".format(
                username=username, backend_name=backend_name)
        )
        message = _(
            "You've successfully logged into your {provider_name} account, "
            "but this account isn't linked with an {platform_name} account yet."
        ).format(
            platform_name=platform_name,
            provider_name=requested_provider.name,
        )
        message += "<br/><br/>"
        message += _(
            "Use your {platform_name} username and password to log into {platform_name} below, "
            "and then link your {platform_name} account with {provider_name} from your dashboard."
        ).format(
            platform_name=platform_name,
            provider_name=requested_provider.name,
        )
        message += "<br/><br/>"
        message += _(
            "If you don't have an {platform_name} account yet, "
            "click <strong>Register</strong> at the top of the page."
        ).format(
            platform_name=platform_name
        )

        raise AuthFailedError(message)


def _get_user_by_email(request):
    """
    Finds a user object in the database based on the given request, ignores all fields except for email.
    """
    if 'email' not in request.POST or 'password' not in request.POST:
        raise AuthFailedError(_('There was an error receiving your login information. Please email us.'))

    email = request.POST['email']

    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            AUDIT_LOG.warning(u"Login failed - Unknown user email")
        else:
            AUDIT_LOG.warning(u"Login failed - Unknown user email: {0}".format(email))


def _check_shib_redirect(user):
    """
    See if the user has a linked shibboleth account, if so, redirect the user to shib-login.
    This behavior is pretty much like what gmail does for shibboleth.  Try entering some @stanford.edu
    address into the Gmail login.
    """
    if settings.FEATURES.get('AUTH_USE_SHIB') and user:
        try:
            eamap = ExternalAuthMap.objects.get(user=user)
            if eamap.external_domain.startswith(openedx.core.djangoapps.external_auth.views.SHIBBOLETH_DOMAIN_PREFIX):
                raise AuthFailedError('', redirect=reverse('shib-login'))
        except ExternalAuthMap.DoesNotExist:
            # This is actually the common case, logging in user without external linked login
            AUDIT_LOG.info(u"User %s w/o external auth attempting login", user)


def _check_excessive_login_attempts(user):
    """
    See if account has been locked out due to excessive login failures
    """
    if user and LoginFailures.is_feature_enabled():
        if LoginFailures.is_user_locked_out(user):
            raise AuthFailedError(_('This account has been temporarily locked due '
                                    'to excessive login failures. Try again later.'))


def _check_forced_password_reset(user):
    """
    See if the user must reset his/her password due to any policy settings
    """
    if user and PasswordHistory.should_user_reset_password_now(user):
        raise AuthFailedError(_('Your password has expired due to password policy on this account. You must '
                                'reset your password before you can log in again. Please click the '
                                '"Forgot Password" link on this page to reset your password before logging in again.'))


def _enforce_password_policy_compliance(request, user):
    try:
        password_policy_compliance.enforce_compliance_on_login(user, request.POST.get('password'))
    except password_policy_compliance.NonCompliantPasswordWarning as e:
        # Allow login, but warn the user that they will be required to reset their password soon.
        PageLevelMessages.register_warning_message(request, e.message)
    except password_policy_compliance.NonCompliantPasswordException as e:
        # Prevent the login attempt.
        raise AuthFailedError(e.message)


def _generate_not_activated_message(user):
    """
    Generates the message displayed on the sign-in screen when a learner attempts to access the
    system with an inactive account.
    """

    support_url = configuration_helpers.get_value(
        'SUPPORT_SITE_LINK',
        settings.SUPPORT_SITE_LINK
    )

    platform_name = configuration_helpers.get_value(
        'PLATFORM_NAME',
        settings.PLATFORM_NAME
    )

    not_activated_msg_template = _('In order to sign in, you need to activate your account.<br /><br />'
                                   'We just sent an activation link to <strong>{email}</strong>.  If '
                                   'you do not receive an email, check your spam folders or '
                                   '<a href="{support_url}">contact {platform} Support</a>.')

    not_activated_message = not_activated_msg_template.format(
        email=user.email,
        support_url=support_url,
        platform=platform_name
    )

    return not_activated_message


def _log_and_raise_inactive_user_auth_error(unauthenticated_user):
    """
    Depending on Django version we can get here a couple of ways, but this takes care of logging an auth attempt
    by an inactive user, re-sending the activation email, and raising an error with the correct message.
    """
    if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
        AUDIT_LOG.warning(
            u"Login failed - Account not active for user.id: {0}, resending activation".format(
                unauthenticated_user.id)
        )
    else:
        AUDIT_LOG.warning(u"Login failed - Account not active for user {0}, resending activation".format(
            unauthenticated_user.username)
        )

    send_reactivation_email_for_user(unauthenticated_user)
    raise AuthFailedError(_generate_not_activated_message(unauthenticated_user))


def _authenticate_first_party(request, unauthenticated_user):
    """
    Use Django authentication on the given request, using rate limiting if configured
    """

    # If the user doesn't exist, we want to set the username to an invalid username so that authentication is guaranteed
    # to fail and we can take advantage of the ratelimited backend
    username = unauthenticated_user.username if unauthenticated_user else ""

    try:
        return authenticate(
            username=username,
            password=request.POST['password'],
            request=request)

    # This occurs when there are too many attempts from the same IP address
    except RateLimitException:
        raise AuthFailedError(_('Too many failed login attempts. Try again later.'))


def _handle_failed_authentication(user):
    """
    Handles updating the failed login count, inactive user notifications, and logging failed authentications.
    """
    if user:
        if LoginFailures.is_feature_enabled():
            LoginFailures.increment_lockout_counter(user)

        if not user.is_active:
            _log_and_raise_inactive_user_auth_error(user)

        # if we didn't find this username earlier, the account for this email
        # doesn't exist, and doesn't have a corresponding password
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            loggable_id = user.id if user else "<unknown>"
            AUDIT_LOG.warning(u"Login failed - password for user.id: {0} is invalid".format(loggable_id))
        else:
            AUDIT_LOG.warning(u"Login failed - password for {0} is invalid".format(user.email))

    raise AuthFailedError(_('Email or password is incorrect.'))


def _handle_successful_authentication_and_login(user, request):
    """
    Handles clearing the failed login counter, login tracking, and setting session timeout.
    """
    if LoginFailures.is_feature_enabled():
        LoginFailures.clear_lockout_counter(user)

    _track_user_login(user, request)

    try:
        django_login(request, user)
        if request.POST.get('remember') == 'true':
            request.session.set_expiry(604800)
            log.debug("Setting user session to never expire")
        else:
            request.session.set_expiry(0)
    except Exception as exc:  # pylint: disable=broad-except
        AUDIT_LOG.critical("Login failed - Could not create session. Is memcached running?")
        log.critical("Login failed - Could not create session. Is memcached running?")
        log.exception(exc)
        raise


def _track_user_login(user, request):
    """
    Sends a tracking event for a successful login.
    """
    if hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
        tracking_context = tracker.get_tracker().resolve_context()
        analytics.identify(
            user.id,
            {
                'email': request.POST['email'],
                'username': user.username
            },
            {
                # Disable MailChimp because we don't want to update the user's email
                # and username in MailChimp on every page load. We only need to capture
                # this data on registration/activation.
                'MailChimp': False
            }
        )

        analytics.track(
            user.id,
            "edx.bi.user.account.authenticated",
            {
                'category': "conversion",
                'label': request.POST.get('course_id'),
                'provider': None
            },
            context={
                'ip': tracking_context.get('ip'),
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )


def send_reactivation_email_for_user(user):
    try:
        registration = Registration.objects.get(user=user)
    except Registration.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('No inactive user with this e-mail exists'),
        })

    try:
        context = generate_activation_email_context(user, registration)
    except ObjectDoesNotExist:
        log.error(
            u'Unable to send reactivation email due to unavailable profile for the user "%s"',
            user.username,
            exc_info=True
        )
        return JsonResponse({
            "success": False,
            "error": _('Unable to send reactivation email')
        })

    subject = render_to_string('emails/activation_email_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', context)
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    from_address = configuration_helpers.get_value('ACTIVATION_EMAIL_FROM_ADDRESS', from_address)

    try:
        user.email_user(subject, message, from_address)
    except Exception:  # pylint: disable=broad-except
        log.error(
            u'Unable to send reactivation email from "%s" to "%s"',
            from_address,
            user.email,
            exc_info=True
        )
        return JsonResponse({
            "success": False,
            "error": _('Unable to send reactivation email')
        })

    return JsonResponse({"success": True})


@login_required
@ensure_csrf_cookie
def verify_user_password(request):
    """
    If the user is logged in and we want to verify that they have submitted the correct password
    for a major account change (for example, retiring this user's account).

    Args:
        request (HttpRequest): A request object where the password should be included in the POST fields.
    """
    try:
        _check_excessive_login_attempts(request.user)
        user = authenticate(username=request.user.username, password=request.POST['password'], request=request)
        if user:
            if LoginFailures.is_feature_enabled():
                LoginFailures.clear_lockout_counter(user)
            return JsonResponse({'success': True})
        else:
            _handle_failed_authentication(request.user)
    except AuthFailedError as err:
        return HttpResponse(err.value, content_type="text/plain", status=403)
    except Exception:  # pylint: disable=broad-except
        log.exception("Could not verify user password")
        return HttpResponseBadRequest()


@ensure_csrf_cookie_cross_domain
@require_POST
def login_user(request):
    """
    AJAX request to log in the user.
    """
    third_party_auth_requested = third_party_auth.is_enabled() and pipeline.running(request)
    trumped_by_first_party_auth = bool(request.POST.get('email')) or bool(request.POST.get('password'))
    was_authenticated_third_party = False

    try:
        if third_party_auth_requested and not trumped_by_first_party_auth:
            # The user has already authenticated via third-party auth and has not
            # asked to do first party auth by supplying a username or password. We
            # now want to put them through the same logging and cookie calculation
            # logic as with first-party auth.

            # This nested try is due to us only returning an HttpResponse in this
            # one case vs. JsonResponse everywhere else.
            try:
                email_user = _do_third_party_auth(request)
                was_authenticated_third_party = True
            except AuthFailedError as e:
                return HttpResponse(e.value, content_type="text/plain", status=403)
        else:
            email_user = _get_user_by_email(request)

        _check_shib_redirect(email_user)
        _check_excessive_login_attempts(email_user)
        _check_forced_password_reset(email_user)

        possibly_authenticated_user = email_user

        if not was_authenticated_third_party:
            possibly_authenticated_user = _authenticate_first_party(request, email_user)
            if possibly_authenticated_user and password_policy_compliance.should_enforce_compliance_on_login():
                # Important: This call must be made AFTER the user was successfully authenticated.
                _enforce_password_policy_compliance(request, possibly_authenticated_user)

        if possibly_authenticated_user is None or not possibly_authenticated_user.is_active:
            _handle_failed_authentication(email_user)

        _handle_successful_authentication_and_login(possibly_authenticated_user, request)

        redirect_url = None  # The AJAX method calling should know the default destination upon success
        if was_authenticated_third_party:
            running_pipeline = pipeline.get(request)
            redirect_url = pipeline.get_complete_url(backend_name=running_pipeline['backend'])

        response = JsonResponse({
            'success': True,
            'redirect_url': redirect_url,
        })

        # Ensure that the external marketing site can
        # detect that the user is logged in.
        return set_logged_in_cookies(request, response, possibly_authenticated_user)
    except AuthFailedError as error:
        return JsonResponse(error.get_response())


@csrf_exempt
@require_POST
@social_utils.psa("social:complete")
def login_oauth_token(request, backend):
    """
    Authenticate the client using an OAuth access token by using the token to
    retrieve information from a third party and matching that information to an
    existing user.
    """
    warnings.warn("Please use AccessTokenExchangeView instead.", DeprecationWarning)

    backend = request.backend
    if isinstance(backend, social_oauth.BaseOAuth1) or isinstance(backend, social_oauth.BaseOAuth2):
        if "access_token" in request.POST:
            # Tell third party auth pipeline that this is an API call
            request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_LOGIN_API
            user = None
            access_token = request.POST["access_token"]
            try:
                user = backend.do_auth(access_token)
            except (HTTPError, AuthException):
                pass
            # do_auth can return a non-User object if it fails
            if user and isinstance(user, User):
                django_login(request, user)
                return JsonResponse(status=204)
            else:
                # Ensure user does not re-enter the pipeline
                request.social_strategy.clean_partial_pipeline(access_token)
                return JsonResponse({"error": "invalid_token"}, status=401)
        else:
            return JsonResponse({"error": "invalid_request"}, status=400)
    raise Http404


@ensure_csrf_cookie
def signin_user(request):
    """Deprecated. To be replaced by :class:`student_account.views.login_and_registration_form`."""
    external_auth_response = external_auth_login(request)
    if external_auth_response is not None:
        return external_auth_response
    # Determine the URL to redirect to following login:
    redirect_to = get_next_url_for_login_page(request)
    if request.user.is_authenticated:
        return redirect(redirect_to)

    third_party_auth_error = None
    for msg in messages.get_messages(request):
        if msg.extra_tags.split()[0] == "social-auth":
            # msg may or may not be translated. Try translating [again] in case we are able to:
            third_party_auth_error = _(text_type(msg))  # pylint: disable=translation-of-non-string
            break

    context = {
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in the header
        # Bool injected into JS to submit form if we're inside a running third-
        # party auth pipeline; distinct from the actual instance of the running
        # pipeline, if any.
        'pipeline_running': 'true' if pipeline.running(request) else 'false',
        'pipeline_url': auth_pipeline_urls(pipeline.AUTH_ENTRY_LOGIN, redirect_url=redirect_to),
        'platform_name': configuration_helpers.get_value(
            'platform_name',
            settings.PLATFORM_NAME
        ),
        'third_party_auth_error': third_party_auth_error
    }

    return render_to_response('login.html', context)


def str2bool(s):
    s = str(s)
    return s.lower() in ('yes', 'true', 't', '1')


def _clean_roles(roles):
    """ Clean roles.

    Strips whitespace from roles, and removes empty items.

    Args:
        roles (str[]): List of role names.

    Returns:
        str[]
    """
    roles = [role.strip() for role in roles]
    roles = [role for role in roles if role]
    return roles


def auto_auth(request):
    """
    Create or configure a user account, then log in as that user.

    Enabled only when
    settings.FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] is true.

    Accepts the following querystring parameters:
    * `username`, `email`, and `password` for the user account
    * `full_name` for the user profile (the user's full name; defaults to the username)
    * `staff`: Set to "true" to make the user global staff.
    * `course_id`: Enroll the student in the course with `course_id`
    * `roles`: Comma-separated list of roles to grant the student in the course with `course_id`
    * `no_login`: Define this to create the user but not login
    * `redirect`: Set to "true" will redirect to the `redirect_to` value if set, or
        course home page if course_id is defined, otherwise it will redirect to dashboard
    * `redirect_to`: will redirect to to this url
    * `is_active` : make/update account with status provided as 'is_active'
    If username, email, or password are not provided, use
    randomly generated credentials.
    """

    # Generate a unique name to use if none provided
    generated_username = uuid.uuid4().hex[0:30]
    generated_password = generate_password()

    # Use the params from the request, otherwise use these defaults
    username = request.GET.get('username', generated_username)
    password = request.GET.get('password', generated_password)
    email = request.GET.get('email', username + "@example.com")
    full_name = request.GET.get('full_name', username)
    is_staff = str2bool(request.GET.get('staff', False))
    is_superuser = str2bool(request.GET.get('superuser', False))
    course_id = request.GET.get('course_id')
    redirect_to = request.GET.get('redirect_to')
    is_active = str2bool(request.GET.get('is_active', True))

    # Valid modes: audit, credit, honor, no-id-professional, professional, verified
    enrollment_mode = request.GET.get('enrollment_mode', 'honor')

    # Parse roles, stripping whitespace, and filtering out empty strings
    roles = _clean_roles(request.GET.get('roles', '').split(','))
    course_access_roles = _clean_roles(request.GET.get('course_access_roles', '').split(','))

    redirect_when_done = str2bool(request.GET.get('redirect', '')) or redirect_to
    login_when_done = 'no_login' not in request.GET

    restricted = settings.FEATURES.get('RESTRICT_AUTOMATIC_AUTH', True)
    if is_superuser and restricted:
        return HttpResponseForbidden(_('Superuser creation not allowed'))

    form = AccountCreationForm(
        data={
            'username': username,
            'email': email,
            'password': password,
            'name': full_name,
        },
        tos_required=False
    )

    # Attempt to create the account.
    # If successful, this will return a tuple containing
    # the new user object.
    try:
        user, profile, reg = do_create_account(form)
    except (AccountValidationError, ValidationError):
        if restricted:
            return HttpResponseForbidden(_('Account modification not allowed.'))
        # Attempt to retrieve the existing user.
        user = User.objects.get(username=username)
        user.email = email
        user.set_password(password)
        user.is_active = is_active
        user.save()
        profile = UserProfile.objects.get(user=user)
        reg = Registration.objects.get(user=user)
    except PermissionDenied:
        return HttpResponseForbidden(_('Account creation not allowed.'))

    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()

    if is_active:
        reg.activate()
        reg.save()

    # ensure parental consent threshold is met
    year = datetime.date.today().year
    age_limit = settings.PARENTAL_CONSENT_AGE_LIMIT
    profile.year_of_birth = (year - age_limit) - 1
    profile.save()

    create_or_set_user_attribute_created_on_site(user, request.site)

    # Enroll the user in a course
    course_key = None
    if course_id:
        course_key = CourseLocator.from_string(course_id)
        CourseEnrollment.enroll(user, course_key, mode=enrollment_mode)

        # Apply the roles
        for role in roles:
            assign_role(course_key, user, role)

        for role in course_access_roles:
            CourseAccessRole.objects.update_or_create(user=user, course_id=course_key, org=course_key.org, role=role)

    # Log in as the user
    if login_when_done:
        user = authenticate_new_user(request, username, password)
        django_login(request, user)

    create_comments_service_user(user)

    if redirect_when_done:
        if redirect_to:
            # Redirect to page specified by the client
            redirect_url = redirect_to
        elif course_id:
            # Redirect to the course homepage (in LMS) or outline page (in Studio)
            try:
                redirect_url = reverse(course_home_url_name(course_key), kwargs={'course_id': course_id})
            except NoReverseMatch:
                redirect_url = reverse('course_handler', kwargs={'course_key_string': course_id})
        else:
            # Redirect to the learner dashboard (in LMS) or homepage (in Studio)
            try:
                redirect_url = reverse('dashboard')
            except NoReverseMatch:
                redirect_url = reverse('home')

        return redirect(redirect_url)
    else:
        response = JsonResponse({
            'created_status': 'Logged in' if login_when_done else 'Created',
            'username': username,
            'email': email,
            'password': password,
            'user_id': user.id,  # pylint: disable=no-member
            'anonymous_id': anonymous_id_for_user(user, None),
        })
    response.set_cookie('csrftoken', csrf(request)['csrf_token'])
    return response


class LogoutView(TemplateView):
    """
    Logs out user and redirects.

    The template should load iframes to log the user out of OpenID Connect services.
    See http://openid.net/specs/openid-connect-logout-1_0.html.
    """
    oauth_client_ids = []
    template_name = 'logout.html'

    # Keep track of the page to which the user should ultimately be redirected.
    default_target = reverse_lazy('cas-logout') if settings.FEATURES.get('AUTH_USE_CAS') else '/'

    @property
    def target(self):
        """
        If a redirect_url is specified in the querystring for this request, and the value is a url
        with the same host, the view will redirect to this page after rendering the template.
        If it is not specified, we will use the default target url.
        """
        target_url = self.request.GET.get('redirect_url')

        if target_url and is_safe_url(target_url, allowed_hosts={self.request.META.get('HTTP_HOST')}, require_https=True):
            return target_url
        else:
            return self.default_target

    def dispatch(self, request, *args, **kwargs):  # pylint: disable=missing-docstring
        # We do not log here, because we have a handler registered to perform logging on successful logouts.
        request.is_from_logout = True

        # Get the list of authorized clients before we clear the session.
        self.oauth_client_ids = request.session.get(edx_oauth2_provider.constants.AUTHORIZED_CLIENTS_SESSION_KEY, [])

        logout(request)

        # If we don't need to deal with OIDC logouts, just redirect the user.
        if self.oauth_client_ids:
            response = super(LogoutView, self).dispatch(request, *args, **kwargs)
        else:
            response = redirect(self.target)

        # Clear the cookie used by the edx.org marketing site
        delete_logged_in_cookies(response)

        return response

    def _build_logout_url(self, url):
        """
        Builds a logout URL with the `no_redirect` query string parameter.

        Args:
            url (str): IDA logout URL

        Returns:
            str
        """
        scheme, netloc, path, query_string, fragment = urlsplit(url)
        query_params = parse_qs(query_string)
        query_params['no_redirect'] = 1
        new_query_string = urlencode(query_params, doseq=True)
        return urlunsplit((scheme, netloc, path, new_query_string, fragment))

    def get_context_data(self, **kwargs):
        context = super(LogoutView, self).get_context_data(**kwargs)

        # Create a list of URIs that must be called to log the user out of all of the IDAs.
        uris = Client.objects.filter(client_id__in=self.oauth_client_ids,
                                     logout_uri__isnull=False).values_list('logout_uri', flat=True)

        referrer = self.request.META.get('HTTP_REFERER', '').strip('/')
        logout_uris = []

        for uri in uris:
            if not referrer or (referrer and not uri.startswith(referrer)):
                logout_uris.append(self._build_logout_url(uri))

        context.update({
            'target': self.target,
            'logout_uris': logout_uris,
        })

        return context
