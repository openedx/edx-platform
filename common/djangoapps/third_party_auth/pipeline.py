"""Auth pipeline definitions.

Auth pipelines handle the process of authenticating a user. They involve a
consumer system and a provider service. The general pattern is:

    1. The consumer system exposes a URL endpoint that starts the process.
    2. When a user visits that URL, the client system redirects the user to a
       page served by the provider. The user authenticates with the provider.
       The provider handles authentication failure however it wants.
    3. On success, the provider POSTs to a URL endpoint on the consumer to
       invoke the pipeline. It sends back an arbitrary payload of data about
       the user.
    4. The pipeline begins, executing each function in its stack. The stack is
       defined on django's settings object's SOCIAL_AUTH_PIPELINE. This is done
       in settings._set_global_settings.
    5. Each pipeline function is variadic. Most pipeline functions are part of
       the pythons-social-auth library; our extensions are defined below. The
       pipeline is the same no matter what provider is used.
    6. Pipeline functions can return a dict to add arguments to the function
       invoked next. They can return None if this is not necessary.
    7. Pipeline functions may be decorated with @partial.partial. This pauses
       the pipeline and serializes its state onto the request's session. When
       this is done they may redirect to other edX handlers to execute edX
       account registration/sign in code.
    8. In that code, redirecting to get_complete_url() resumes the pipeline.
       This happens by hitting a handler exposed by the consumer system.
    9. In this way, execution moves between the provider, the pipeline, and
       arbitrary consumer system code.

Gotcha alert!:

Bear in mind that when pausing and resuming a pipeline function decorated with
@partial.partial, execution resumes by re-invoking the decorated function
instead of invoking the next function in the pipeline stack. For example, if
you have a pipeline of

    A
    B
    C

with an implementation of

    @partial.partial
    def B(*args, **kwargs):
        [...]

B will be invoked twice: once when initially proceeding through the pipeline
before it is paused, and once when other code finishes and the pipeline
resumes. Consequently, many decorated functions will first invoke a predicate
to determine if they are in their first or second execution (usually by
checking side-effects from the first run).

This is surprising but important behavior, since it allows a single function in
the pipeline to consolidate all the operations needed to establish invariants
rather than spreading them across two functions in the pipeline.

See http://psa.matiasaguirre.net/docs/pipeline.html for more docs.
"""

import random
import string  # pylint: disable-msg=deprecated-module
from collections import OrderedDict
import urllib
from ipware.ip import get_ip
import analytics
from eventtracking import tracker

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from social.apps.django_app.default import models
from social.exceptions import AuthException
from social.pipeline import partial
from social.pipeline.social_auth import associate_by_email

import student
from embargo import api as embargo_api
from shoppingcart.models import Order, PaidCourseRegistration  # pylint: disable=import-error
from shoppingcart.exceptions import (  # pylint: disable=import-error
    CourseDoesNotExistException,
    ItemAlreadyInCartException,
    AlreadyEnrolledInCourseException
)
from student.models import CourseEnrollment, CourseEnrollmentException
from course_modes.models import CourseMode
from opaque_keys.edx.keys import CourseKey

from logging import getLogger

from . import provider

# Note that this lives in openedx, so this dependency should be refactored.
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in


# These are the query string params you can pass
# to the URL that starts the authentication process.
#
# `AUTH_ENTRY_KEY` is required and indicates how the user
# enters the authentication process.
#
# `AUTH_REDIRECT_KEY` provides an optional URL to redirect
# to upon successful authentication
# (if not provided, defaults to `_SOCIAL_AUTH_LOGIN_REDIRECT_URL`)
#
# `AUTH_ENROLL_COURSE_ID_KEY` provides the course ID that a student
# is trying to enroll in, used to generate analytics events
# and auto-enroll students.
AUTH_ENTRY_KEY = 'auth_entry'
AUTH_REDIRECT_KEY = 'next'
AUTH_ENROLL_COURSE_ID_KEY = 'enroll_course_id'
AUTH_EMAIL_OPT_IN_KEY = 'email_opt_in'


# The following are various possible values for the AUTH_ENTRY_KEY.
AUTH_ENTRY_LOGIN = 'login'
AUTH_ENTRY_REGISTER = 'register'
AUTH_ENTRY_ACCOUNT_SETTINGS = 'account_settings'

# This is left-over from an A/B test
# of the new combined login/registration page (ECOM-369)
# We need to keep both the old and new entry points
# until every session from before the test ended has expired.
AUTH_ENTRY_LOGIN_2 = 'account_login'
AUTH_ENTRY_REGISTER_2 = 'account_register'

# Entry modes into the authentication process by a remote API call (as opposed to a browser session).
AUTH_ENTRY_LOGIN_API = 'login_api'
AUTH_ENTRY_REGISTER_API = 'register_api'


def is_api(auth_entry):
    """Returns whether the auth entry point is via an API call."""
    return (auth_entry == AUTH_ENTRY_LOGIN_API) or (auth_entry == AUTH_ENTRY_REGISTER_API)

# URLs associated with auth entry points
# These are used to request additional user information
# (for example, account credentials when logging in),
# and when the user cancels the auth process
# (e.g., refusing to grant permission on the provider's login page).
# We don't use "reverse" here because doing so may cause modules
# to load that depend on this module.
AUTH_DISPATCH_URLS = {
    AUTH_ENTRY_LOGIN: '/login',
    AUTH_ENTRY_REGISTER: '/register',
    AUTH_ENTRY_ACCOUNT_SETTINGS: '/account/settings',

    # This is left-over from an A/B test
    # of the new combined login/registration page (ECOM-369)
    # We need to keep both the old and new entry points
    # until every session from before the test ended has expired.
    AUTH_ENTRY_LOGIN_2: '/account/login/',
    AUTH_ENTRY_REGISTER_2: '/account/register/',

}

_AUTH_ENTRY_CHOICES = frozenset([
    AUTH_ENTRY_LOGIN,
    AUTH_ENTRY_REGISTER,
    AUTH_ENTRY_ACCOUNT_SETTINGS,

    # This is left-over from an A/B test
    # of the new combined login/registration page (ECOM-369)
    # We need to keep both the old and new entry points
    # until every session from before the test ended has expired.
    AUTH_ENTRY_LOGIN_2,
    AUTH_ENTRY_REGISTER_2,

    AUTH_ENTRY_LOGIN_API,
    AUTH_ENTRY_REGISTER_API,
])

_DEFAULT_RANDOM_PASSWORD_LENGTH = 12
_PASSWORD_CHARSET = string.letters + string.digits

logger = getLogger(__name__)


class AuthEntryError(AuthException):
    """Raised when auth_entry is missing or invalid on URLs.

    auth_entry tells us whether the auth flow was initiated to register a new
    user (in which case it has the value of AUTH_ENTRY_REGISTER) or log in an
    existing user (in which case it has the value of AUTH_ENTRY_LOGIN).

    This is necessary because the edX code we hook into the pipeline to
    redirect to the existing auth flows needs to know what case we are in in
    order to format its output correctly (for example, the register code is
    invoked earlier than the login code, and it needs to know if the login flow
    was requested to dispatch correctly).
    """


class ProviderUserState(object):
    """Object representing the provider state (attached or not) for a user.

    This is intended only for use when rendering templates. See for example
    lms/templates/dashboard.html.
    """

    def __init__(self, enabled_provider, user, state):
        # Boolean. Whether the user has an account associated with the provider
        self.has_account = state
        # provider.BaseProvider child. Callers must verify that the provider is
        # enabled.
        self.provider = enabled_provider
        # django.contrib.auth.models.User.
        self.user = user

    def get_unlink_form_name(self):
        """Gets the name used in HTML forms that unlink a provider account."""
        return self.provider.NAME + '_unlink_form'


def get(request):
    """Gets the running pipeline from the passed request."""
    return request.session.get('partial_pipeline')


def get_authenticated_user(username, backend_name):
    """Gets a saved user authenticated by a particular backend.

    Between pipeline steps User objects are not saved. We need to reconstitute
    the user and set its .backend, which is ordinarily monkey-patched on by
    Django during authenticate(), so it will function like a user returned by
    authenticate().

    Args:
        username: string. Username of user to get.
        backend_name: string. The name of the third-party auth backend from
            the running pipeline.

    Returns:
        User if user is found and has a social auth from the passed
        backend_name.

    Raises:
        User.DoesNotExist: if no user matching user is found, or the matching
        user has no social auth associated with the given backend.
        AssertionError: if the user is not authenticated.
    """
    user = models.DjangoStorage.user.user_model().objects.get(username=username)
    match = models.DjangoStorage.user.get_social_auth_for_user(user, provider=backend_name)

    if not match:
        raise User.DoesNotExist

    user.backend = provider.Registry.get_by_backend_name(backend_name).get_authentication_backend()
    return user


def _get_enabled_provider_by_name(provider_name):
    """Gets an enabled provider by its NAME member or throws."""
    enabled_provider = provider.Registry.get(provider_name)

    if not enabled_provider:
        raise ValueError('Provider %s not enabled' % provider_name)

    return enabled_provider


def _get_url(view_name, backend_name, auth_entry=None, redirect_url=None, enroll_course_id=None, email_opt_in=None):
    """Creates a URL to hook into social auth endpoints."""
    kwargs = {'backend': backend_name}
    url = reverse(view_name, kwargs=kwargs)

    query_params = OrderedDict()
    if auth_entry:
        query_params[AUTH_ENTRY_KEY] = auth_entry

    if redirect_url:
        query_params[AUTH_REDIRECT_KEY] = redirect_url

    if enroll_course_id:
        query_params[AUTH_ENROLL_COURSE_ID_KEY] = enroll_course_id

    if email_opt_in:
        query_params[AUTH_EMAIL_OPT_IN_KEY] = email_opt_in

    return u"{url}?{params}".format(
        url=url,
        params=urllib.urlencode(query_params)
    )


def get_complete_url(backend_name):
    """Gets URL for the endpoint that returns control to the auth pipeline.

    Args:
        backend_name: string. Name of the python-social-auth backend from the
            currently-running pipeline.

    Returns:
        String. URL that finishes the auth pipeline for a provider.

    Raises:
        ValueError: if no provider is enabled with the given backend_name.
    """
    enabled_provider = provider.Registry.get_by_backend_name(backend_name)

    if not enabled_provider:
        raise ValueError('Provider with backend %s not enabled' % backend_name)

    return _get_url('social:complete', backend_name)


def get_disconnect_url(provider_name):
    """Gets URL for the endpoint that starts the disconnect pipeline.

    Args:
        provider_name: string. Name of the provider.BaseProvider child you want
            to disconnect from.

    Returns:
        String. URL that starts the disconnection pipeline.

    Raises:
        ValueError: if no provider is enabled with the given backend_name.
    """
    enabled_provider = _get_enabled_provider_by_name(provider_name)
    return _get_url('social:disconnect', enabled_provider.BACKEND_CLASS.name)


def get_login_url(provider_name, auth_entry, redirect_url=None, enroll_course_id=None, email_opt_in=None):
    """Gets the login URL for the endpoint that kicks off auth with a provider.

    Args:
        provider_name: string. The name of the provider.Provider that has been
            enabled.
        auth_entry: string. Query argument specifying the desired entry point
            for the auth pipeline. Used by the pipeline for later branching.
            Must be one of _AUTH_ENTRY_CHOICES.

    Keyword Args:
        redirect_url (string): If provided, redirect to this URL at the end
            of the authentication process.

        enroll_course_id (string): If provided, auto-enroll the user in this
            course upon successful authentication.

        email_opt_in (string): If set to 'true' (case insensitive), user will
            be opted into organization-wide email. Any other string will
            equate to False, and the user will be opted out of organization-wide
            email.

    Returns:
        String. URL that starts the auth pipeline for a provider.

    Raises:
        ValueError: if no provider is enabled with the given provider_name.
    """
    assert auth_entry in _AUTH_ENTRY_CHOICES
    enabled_provider = _get_enabled_provider_by_name(provider_name)
    return _get_url(
        'social:begin',
        enabled_provider.BACKEND_CLASS.name,
        auth_entry=auth_entry,
        redirect_url=redirect_url,
        enroll_course_id=enroll_course_id,
        email_opt_in=email_opt_in
    )


def get_duplicate_provider(messages):
    """Gets provider from message about social account already in use.

    python-social-auth's exception middleware uses the messages module to
    record details about duplicate account associations. It records exactly one
    message there is a request to associate a social account S with an edX
    account E if S is already associated with an edX account E'.

    This messaging approach is stringly-typed and the particular string is
    unfortunately not in a reusable constant.

    Returns:
        provider.BaseProvider child instance. The provider of the duplicate
        account, or None if there is no duplicate (and hence no error).
    """
    social_auth_messages = [m for m in messages if m.message.endswith('is already in use.')]

    if not social_auth_messages:
        return

    assert len(social_auth_messages) == 1
    return provider.Registry.get_by_backend_name(social_auth_messages[0].extra_tags.split()[1])


def get_provider_user_states(user):
    """Gets list of states of provider-user combinations.

    Args:
        django.contrib.auth.User. The user to get states for.

    Returns:
        List of ProviderUserState. The list of states of a user's account with
            each enabled provider.
    """
    states = []
    found_user_backends = [
        social_auth.provider for social_auth in models.DjangoStorage.user.get_social_auth_for_user(user)
    ]

    for enabled_provider in provider.Registry.enabled():
        states.append(
            ProviderUserState(enabled_provider, user, enabled_provider.BACKEND_CLASS.name in found_user_backends)
        )

    return states


def make_random_password(length=None, choice_fn=random.SystemRandom().choice):
    """Makes a random password.

    When a user creates an account via a social provider, we need to create a
    placeholder password for them to satisfy the ORM's consistency and
    validation requirements. Users don't know (and hence cannot sign in with)
    this password; that's OK because they can always use the reset password
    flow to set it to a known value.

    Args:
        choice_fn: function or method. Takes an iterable and returns a random
            element.
        length: int. Number of chars in the returned value. None to use default.

    Returns:
        String. The resulting password.
    """
    length = length if length is not None else _DEFAULT_RANDOM_PASSWORD_LENGTH
    return ''.join(choice_fn(_PASSWORD_CHARSET) for _ in xrange(length))


def running(request):
    """Returns True iff request is running a third-party auth pipeline."""
    return request.session.get('partial_pipeline') is not None  # Avoid False for {}.


# Pipeline functions.
# Signatures are set by python-social-auth; prepending 'unused_' causes
# TypeError on dispatch to the auth backend's authenticate().
# pylint: disable-msg=unused-argument


def parse_query_params(strategy, response, *args, **kwargs):
    """Reads whitelisted query params, transforms them into pipeline args."""
    auth_entry = strategy.session.get(AUTH_ENTRY_KEY)
    if not (auth_entry and auth_entry in _AUTH_ENTRY_CHOICES):
        raise AuthEntryError(strategy.backend, 'auth_entry missing or invalid')

    return {'auth_entry': auth_entry}


@partial.partial
def ensure_user_information(strategy, auth_entry, user=None, *args, **kwargs):
    """
    Ensure that we have the necessary information about a user (either an
    existing account or registration data) to proceed with the pipeline.
    """

    # We're deliberately verbose here to make it clear what the intended
    # dispatch behavior is for the various pipeline entry points, given the
    # current state of the pipeline. Keep in mind the pipeline is re-entrant
    # and values will change on repeated invocations (for example, the first
    # time through the login flow the user will be None so we dispatch to the
    # login form; the second time it will have a value so we continue to the
    # next pipeline step directly).
    #
    # It is important that we always execute the entire pipeline. Even if
    # behavior appears correct without executing a step, it means important
    # invariants have been violated and future misbehavior is likely.
    def dispatch_to_login():
        """Redirects to the login page."""
        return redirect(_create_redirect_url(AUTH_DISPATCH_URLS[AUTH_ENTRY_LOGIN], strategy))

    def dispatch_to_register():
        """Redirects to the registration page."""
        return redirect(_create_redirect_url(AUTH_DISPATCH_URLS[AUTH_ENTRY_REGISTER], strategy))

    user_inactive = user and not user.is_active

    if auth_entry in [AUTH_ENTRY_LOGIN_API, AUTH_ENTRY_REGISTER_API]:
        if not user:
            return HttpResponseBadRequest()

    elif auth_entry in [AUTH_ENTRY_LOGIN, AUTH_ENTRY_LOGIN_2]:
        if not user or user_inactive:
            return dispatch_to_login()

    elif auth_entry in [AUTH_ENTRY_REGISTER, AUTH_ENTRY_REGISTER_2]:
        if not user:
            return dispatch_to_register()
        elif user_inactive:
            # If the user has a linked account, but has not yet activated
            # we should send them to the login page. The login page
            # will tell them that they need to activate their account.
            return dispatch_to_login()


def _create_redirect_url(url, strategy):
    """ Given a URL and a Strategy, construct the appropriate redirect URL.

    Construct a redirect URL and append the URL parameters that should be preserved.

    Args:
        url (string): The base URL to use for the redirect.
        strategy (Strategy): Used to determine which URL parameters to append to the redirect.

    Returns:
        A string representation of the URL, with parameters, for redirect.
    """
    url_params = {}
    enroll_course_id = strategy.session_get(AUTH_ENROLL_COURSE_ID_KEY)
    if enroll_course_id:
        url_params['course_id'] = enroll_course_id
        url_params['enrollment_action'] = 'enroll'
    email_opt_in = strategy.session_get(AUTH_EMAIL_OPT_IN_KEY)
    if email_opt_in:
        url_params[AUTH_EMAIL_OPT_IN_KEY] = email_opt_in
    if url_params:
        return u'{url}?{params}'.format(
            url=url,
            params=urllib.urlencode(url_params)
        )
    else:
        return url


@partial.partial
def set_logged_in_cookie(backend=None, user=None, request=None, auth_entry=None, *args, **kwargs):
    """This pipeline step sets the "logged in" cookie for authenticated users.

    Some installations have a marketing site front-end separate from
    edx-platform.  Those installations sometimes display different
    information for logged in versus anonymous users (e.g. a link
    to the student dashboard instead of the login page.)

    Since social auth uses Django's native `login()` method, it bypasses
    our usual login view that sets this cookie.  For this reason, we need
    to set the cookie ourselves within the pipeline.

    The procedure for doing this is a little strange.  On the one hand,
    we need to send a response to the user in order to set the cookie.
    On the other hand, we don't want to drop the user out of the pipeline.

    For this reason, we send a redirect back to the "complete" URL,
    so users immediately re-enter the pipeline.  The redirect response
    contains a header that sets the logged in cookie.

    If the user is not logged in, or the logged in cookie is already set,
    the function returns `None`, indicating that control should pass
    to the next pipeline step.

    """
    if not is_api(auth_entry) and user is not None and user.is_authenticated():
        if request is not None:
            # Check that the cookie isn't already set.
            # This ensures that we allow the user to continue to the next
            # pipeline step once he/she has the cookie set by this step.
            has_cookie = student.helpers.is_logged_in_cookie_set(request)
            if not has_cookie:
                try:
                    redirect_url = get_complete_url(backend.name)
                except ValueError:
                    # If for some reason we can't get the URL, just skip this step
                    # This may be overly paranoid, but it's far more important that
                    # the user log in successfully than that the cookie is set.
                    pass
                else:
                    response = redirect(redirect_url)
                    return student.helpers.set_logged_in_cookie(request, response)


@partial.partial
def login_analytics(strategy, auth_entry, *args, **kwargs):
    """ Sends login info to Segment.io """

    event_name = None
    if auth_entry in [AUTH_ENTRY_LOGIN, AUTH_ENTRY_LOGIN_2]:
        event_name = 'edx.bi.user.account.authenticated'
    elif auth_entry in [AUTH_ENTRY_ACCOUNT_SETTINGS]:
        event_name = 'edx.bi.user.account.linked'

    if event_name is not None:
        tracking_context = tracker.get_tracker().resolve_context()
        analytics.track(
            kwargs['user'].id,
            event_name,
            {
                'category': "conversion",
                'label': strategy.session_get('enroll_course_id'),
                'provider': getattr(kwargs['backend'], 'name')
            },
            context={
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )


@partial.partial
def change_enrollment(strategy, auth_entry=None, user=None, *args, **kwargs):
    """Enroll a user in a course.

    If a user entered the authentication flow when trying to enroll
    in a course, then attempt to enroll the user.
    We will try to do this if the pipeline was started with the
    querystring param `enroll_course_id`.

    In the following cases, we can't enroll the user:
        * The course does not have an honor mode.
        * The course has an honor mode with a minimum price.
        * The course is not yet open for enrollment.
        * The course does not exist.

    If we can't enroll the user now, then skip this step.
    For paid courses, users will be redirected to the payment flow
    upon completion of the authentication pipeline
    (configured using the ?next parameter to the third party auth login url).

    Keyword Arguments:
        auth_entry: The entry mode into the pipeline.
        user (User): The user being authenticated.
    """
    # We skip enrollment if the user entered the flow from the "link account"
    # button on the account settings page.  At this point, either:
    #
    # 1) The user already had a linked account when they started the enrollment flow,
    # in which case they would have been enrolled during the normal authentication process.
    #
    # 2) The user did NOT have a linked account, in which case they would have
    # needed to go through the login/register page.  Since we preserve the querystring
    # args when sending users to this page, successfully authenticating through this page
    # would also enroll the student in the course.
    enroll_course_id = strategy.session_get('enroll_course_id')
    if enroll_course_id and auth_entry != AUTH_ENTRY_ACCOUNT_SETTINGS:
        course_id = CourseKey.from_string(enroll_course_id)
        modes = CourseMode.modes_for_course_dict(course_id)

        # If the email opt in parameter is found, set the preference.
        email_opt_in = strategy.session_get(AUTH_EMAIL_OPT_IN_KEY)
        if email_opt_in:
            opt_in = email_opt_in.lower() == 'true'
            update_email_opt_in(user, course_id.org, opt_in)

        # Check whether we're blocked from enrolling by a
        # country access rule.
        # Note: We skip checking the user's profile setting
        # for country here because the "redirect URL" pointing
        # to the blocked message page is set when the user
        # *enters* the pipeline, at which point they're
        # not authenticated.  If they end up being blocked
        # from the courseware, it's better to let them
        # enroll and then show the message when they
        # enter the course than to skip enrollment
        # altogether.
        is_blocked = not embargo_api.check_course_access(
            course_id, ip_address=get_ip(strategy.request),
            url=strategy.request.path
        )
        if is_blocked:
            # If we're blocked, skip enrollment.
            # A redirect URL should have been set so the user
            # ends up on the embargo page when enrollment completes.
            pass

        elif CourseMode.can_auto_enroll(course_id, modes_dict=modes):
            try:
                CourseEnrollment.enroll(user, course_id, check_access=True)
            except CourseEnrollmentException:
                pass
            except Exception as ex:
                logger.exception(ex)

        # Handle white-label courses as a special case
        # If a course is white-label, we should add it to the shopping cart.
        elif CourseMode.is_white_label(course_id, modes_dict=modes):
            try:
                cart = Order.get_cart_for_user(user)
                PaidCourseRegistration.add_to_order(cart, course_id)
            except (
                CourseDoesNotExistException,
                ItemAlreadyInCartException,
                AlreadyEnrolledInCourseException,
            ):
                pass
            # It's more important to complete login than to
            # ensure that the course was added to the shopping cart.
            # Log errors, but don't stop the authentication pipeline.
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(ex)


@partial.partial
def associate_by_email_if_login_api(auth_entry, strategy, details, user, *args, **kwargs):
    """
    This pipeline step associates the current social auth with the user with the
    same email address in the database.  It defers to the social library's associate_by_email
    implementation, which verifies that only a single database user is associated with the email.

    This association is done ONLY if the user entered the pipeline through a LOGIN API.
    """
    if auth_entry == AUTH_ENTRY_LOGIN_API:
        association_response = associate_by_email(strategy, details, user, *args, **kwargs)
        if (
            association_response and
            association_response.get('user') and
            association_response['user'].is_active
        ):
            # Only return the user matched by email if their email has been activated.
            # Otherwise, an illegitimate user can create an account with another user's
            # email address and the legitimate user would now login to the illegitimate
            # account.
            return association_response
