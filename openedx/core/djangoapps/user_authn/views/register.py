"""
Registration related views.
"""


import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied
from django.core.validators import ValidationError
from django.db import transaction
from django.dispatch import Signal
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters
from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace
from pytz import UTC
from ratelimit.decorators import ratelimit
from requests import HTTPError
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from social_core.exceptions import AuthAlreadyAssociated, AuthException
from social_django import utils as social_utils

from common.djangoapps import third_party_auth
# Note that this lives in LMS, so this dependency should be refactored.
# TODO Have the discussions code subscribe to the REGISTER_USER signal instead.
from common.djangoapps.student.helpers import get_next_url_for_login_page
from lms.djangoapps.discussion.notification_prefs.views import enable_notifications
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_api.accounts.api import (
    get_confirm_email_validation_error,
    get_country_validation_error,
    get_email_existence_validation_error,
    get_email_validation_error,
    get_name_validation_error,
    get_password_validation_error,
    get_username_existence_validation_error,
    get_username_validation_error
)
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.user_authn.utils import generate_password, is_registration_api_v1
from openedx.core.djangoapps.user_authn.views.registration_form import (
    AccountCreationForm,
    RegistrationFormFactory,
    get_registration_extension_form
)
from common.djangoapps.student.helpers import (
    AccountValidationError,
    authenticate_new_user,
    create_or_set_user_attribute_created_on_site,
    do_create_account
)
from common.djangoapps.student.models import (
    RegistrationCookieConfiguration,
    UserAttribute,
    create_comments_service_user,
    email_exists_or_retired,
    username_exists_or_retired
)
from common.djangoapps.student.views import compose_and_send_activation_email
from common.djangoapps.third_party_auth import pipeline, provider
from common.djangoapps.third_party_auth.saml import SAP_SUCCESSFACTORS_SAML_KEY
from common.djangoapps.track import segment
from common.djangoapps.util.db import outer_atomic
from common.djangoapps.util.json_request import JsonResponse

log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")


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
# used to announce a registration
REGISTER_USER = Signal(providing_args=["user", "registration"])


# .. toggle_name: registration.enable_failure_logging
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enable verbose logging of registration failure messages
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2020-04-30
# .. toggle_target_removal_date: 2020-06-01
# .. toggle_warnings: This temporary feature toggle does not have a target removal date.
# .. toggle_tickets: None
REGISTRATION_FAILURE_LOGGING_FLAG = WaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=u'registration'),
    flag_name=u'enable_failure_logging',
    module_name=__name__,
)
REAL_IP_KEY = 'openedx.core.djangoapps.util.ratelimit.real_ip'


@transaction.non_atomic_requests
def create_account_with_params(request, params):
    """
    Given a request and a dict of parameters (which may or may not have come
    from the request), create an account for the requesting user, including
    creating a comments service user object and sending an activation email.
    This also takes external/third-party auth into account, updates that as
    necessary, and authenticates the user for the request's session.

    Does not return anything.

    Raises AccountValidationError if an account with the username or email
    specified by params already exists, or ValidationError if any of the given
    parameters is invalid for any other reason.

    Issues with this code:
    * It is non-transactional except where explicitly wrapped in atomic to
      alleviate deadlocks and improve performance. This means failures at
      different places in registration can leave users in inconsistent
      states.
    * Third-party auth passwords are not verified. There is a comment that
      they are unused, but it would be helpful to have a sanity check that
      they are sane.
    * The user-facing text is rather unfriendly (e.g. "Username must be a
      minimum of two characters long" rather than "Please use a username of
      at least two characters").
    * Duplicate email raises a ValidationError (rather than the expected
      AccountValidationError). Duplicate username returns an inconsistent
      user message (i.e. "An account with the Public Username '{username}'
      already exists." rather than "It looks like {username} belongs to an
      existing account. Try again with a different username.") The two checks
      occur at different places in the code; as a result, registering with
      both a duplicate username and email raises only a ValidationError for
      email only.
    """
    # Copy params so we can modify it; we can't just do dict(params) because if
    # params is request.POST, that results in a dict containing lists of values
    params = dict(list(params.items()))

    # allow to define custom set of required/optional/hidden fields via configuration
    extra_fields = configuration_helpers.get_value(
        'REGISTRATION_EXTRA_FIELDS',
        getattr(settings, 'REGISTRATION_EXTRA_FIELDS', {})
    )
    if is_registration_api_v1(request):
        if 'confirm_email' in extra_fields:
            del extra_fields['confirm_email']

    # registration via third party (Google, Facebook) using mobile application
    # doesn't use social auth pipeline (no redirect uri(s) etc involved).
    # In this case all related info (required for account linking)
    # is sent in params.
    # `third_party_auth_credentials_in_api` essentially means 'request
    # is made from mobile application'
    third_party_auth_credentials_in_api = 'provider' in params
    is_third_party_auth_enabled = third_party_auth.is_enabled()

    if is_third_party_auth_enabled and (pipeline.running(request) or third_party_auth_credentials_in_api):
        params["password"] = generate_password()

    # in case user is registering via third party (Google, Facebook) and pipeline has expired, show appropriate
    # error message
    if is_third_party_auth_enabled and ('social_auth_provider' in params and not pipeline.running(request)):
        raise ValidationError(
            {'session_expired': [
                _(u"Registration using {provider} has timed out.").format(
                    provider=params.get('social_auth_provider'))
            ]}
        )

    extended_profile_fields = configuration_helpers.get_value('extended_profile_fields', [])
    # Can't have terms of service for certain SHIB users, like at Stanford
    registration_fields = getattr(settings, 'REGISTRATION_EXTRA_FIELDS', {})
    tos_required = (
        registration_fields.get('terms_of_service') != 'hidden' or
        registration_fields.get('honor_code') != 'hidden'
    )

    form = AccountCreationForm(
        data=params,
        extra_fields=extra_fields,
        extended_profile_fields=extended_profile_fields,
        do_third_party_auth=False,
        tos_required=tos_required,
    )
    custom_form = get_registration_extension_form(data=params)

    # Perform operations within a transaction that are critical to account creation
    with outer_atomic(read_committed=True):
        # first, create the account
        (user, profile, registration) = do_create_account(form, custom_form)

        third_party_provider, running_pipeline = _link_user_to_third_party_provider(
            is_third_party_auth_enabled, third_party_auth_credentials_in_api, user, request, params,
        )

        new_user = authenticate_new_user(request, user.username, form.cleaned_data['password'])
        django_login(request, new_user)
        request.session.set_expiry(0)

    # Sites using multiple languages need to record the language used during registration.
    # If not, compose_and_send_activation_email will be sent in site's default language only.
    create_or_set_user_attribute_created_on_site(user, request.site)

    # Only add a default user preference if user does not already has one.
    if not preferences_api.has_user_preference(user, LANGUAGE_KEY):
        preferences_api.set_user_preference(user, LANGUAGE_KEY, get_language())

    # Check if system is configured to skip activation email for the current user.
    skip_email = _skip_activation_email(
        user, running_pipeline, third_party_provider,
    )

    if skip_email:
        registration.activate()
    else:
        compose_and_send_activation_email(user, profile, registration)

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception(u"Enable discussion notifications failed for user {id}.".format(id=user.id))

    _track_user_registration(user, profile, params, third_party_provider)

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)

    create_comments_service_user(user)

    try:
        _record_registration_attributions(request, new_user)
    # Don't prevent a user from registering due to attribution errors.
    except Exception:   # pylint: disable=broad-except
        log.exception('Error while attributing cookies to user registration.')

    # TODO: there is no error checking here to see that the user actually logged in successfully,
    # and is not yet an active user.
    if new_user is not None:
        AUDIT_LOG.info(u"Login success on new account creation - {0}".format(new_user.username))

    return new_user


def _link_user_to_third_party_provider(
    is_third_party_auth_enabled,
    third_party_auth_credentials_in_api,
    user,
    request,
    params,
):
    """
    If a 3rd party auth provider and credentials were provided in the API, link the account with social auth
    (If the user is using the normal register page, the social auth pipeline does the linking, not this code)

    Note: this is orthogonal to the 3rd party authentication pipeline that occurs
    when the account is created via the browser and redirect URLs.
    """
    third_party_provider, running_pipeline = None, None
    if is_third_party_auth_enabled and third_party_auth_credentials_in_api:
        backend_name = params['provider']
        request.social_strategy = social_utils.load_strategy(request)
        redirect_uri = reverse('social:complete', args=(backend_name, ))
        request.backend = social_utils.load_backend(request.social_strategy, backend_name, redirect_uri)
        social_access_token = params.get('access_token')
        if not social_access_token:
            raise ValidationError({
                'access_token': [
                    _(u"An access_token is required when passing value ({}) for provider.").format(
                        params['provider']
                    )
                ]
            })
        request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_REGISTER_API
        pipeline_user = None
        error_message = ""
        try:
            pipeline_user = request.backend.do_auth(social_access_token, user=user)
        except AuthAlreadyAssociated:
            error_message = _("The provided access_token is already associated with another user.")
        except (HTTPError, AuthException):
            error_message = _("The provided access_token is not valid.")
        if not pipeline_user or not isinstance(pipeline_user, User):
            # Ensure user does not re-enter the pipeline
            request.social_strategy.clean_partial_pipeline(social_access_token)
            raise ValidationError({'access_token': [error_message]})

    # If the user is registering via 3rd party auth, track which provider they use
    if is_third_party_auth_enabled and pipeline.running(request):
        running_pipeline = pipeline.get(request)
        third_party_provider = provider.Registry.get_from_pipeline(running_pipeline)

    return third_party_provider, running_pipeline


def _track_user_registration(user, profile, params, third_party_provider):
    """ Track the user's registration. """
    if hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
        identity_args = [
            user.id,
            {
                'email': user.email,
                'username': user.username,
                'name': profile.name,
                # Mailchimp requires the age & yearOfBirth to be integers, we send a sane integer default if falsey.
                'age': profile.age or -1,
                'yearOfBirth': profile.year_of_birth or datetime.datetime.now(UTC).year,
                'education': profile.level_of_education_display,
                'address': profile.mailing_address,
                'gender': profile.gender_display,
                'country': text_type(profile.country),
            }
        ]
        # .. pii: Many pieces of PII are sent to Segment here. Retired directly through Segment API call in Tubular.
        # .. pii_types: email_address, username, name, birth_date, location, gender
        # .. pii_retirement: third_party
        segment.identify(*identity_args)
        segment.track(
            user.id,
            "edx.bi.user.account.registered",
            {
                'category': 'conversion',
                # ..pii: Learner email is sent to Segment in following line and will be associated with analytics data.
                'email': user.email,
                'label': params.get('course_id'),
                'provider': third_party_provider.name if third_party_provider else None
            },
        )


def _skip_activation_email(user, running_pipeline, third_party_provider):
    """
    Return `True` if activation email should be skipped.

    Skip email if we are:
        1. Doing load testing.
        2. Random user generation for other forms of testing.
        3. External auth bypassing activation.
        4. Have the platform configured to not require e-mail activation.
        5. Registering a new user using a trusted third party provider (with skip_email_verification=True)

    Note that this feature is only tested as a flag set one way or
    the other for *new* systems. we need to be careful about
    changing settings on a running system to make sure no users are
    left in an inconsistent state (or doing a migration if they are).

    Arguments:
        user (User): Django User object for the current user.
        running_pipeline (dict): Dictionary containing user and pipeline data for third party authentication.
        third_party_provider (ProviderConfig): An instance of third party provider configuration.

    Returns:
        (bool): `True` if account activation email should be skipped, `False` if account activation email should be
            sent.
    """
    sso_pipeline_email = running_pipeline and running_pipeline['kwargs'].get('details', {}).get('email')

    # Email is valid if the SAML assertion email matches the user account email or
    # no email was provided in the SAML assertion. Some IdP's use a callback
    # to retrieve additional user account information (including email) after the
    # initial account creation.
    valid_email = (
        sso_pipeline_email == user.email or (
            sso_pipeline_email is None and
            third_party_provider and
            getattr(third_party_provider, "identity_provider_type", None) == SAP_SUCCESSFACTORS_SAML_KEY
        )
    )

    # log the cases where skip activation email flag is set, but email validity check fails
    if third_party_provider and third_party_provider.skip_email_verification and not valid_email:
        log.info(
            u'[skip_email_verification=True][user=%s][pipeline-email=%s][identity_provider=%s][provider_type=%s] '
            'Account activation email sent as user\'s system email differs from SSO email.',
            user.email,
            sso_pipeline_email,
            getattr(third_party_provider, "provider_id", None),
            getattr(third_party_provider, "identity_provider_type", None)
        )

    return (
        settings.FEATURES.get('SKIP_EMAIL_VALIDATION', None) or
        settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING') or
        (third_party_provider and third_party_provider.skip_email_verification and valid_email)
    )


def _record_registration_attributions(request, user):
    """
    Attribute this user's registration based on referrer cookies.
    """
    _record_affiliate_registration_attribution(request, user)
    _record_utm_registration_attribution(request, user)


def _record_affiliate_registration_attribution(request, user):
    """
    Attribute this user's registration to the referring affiliate, if
    applicable.
    """
    affiliate_id = request.COOKIES.get(settings.AFFILIATE_COOKIE_NAME)
    if user and affiliate_id:
        UserAttribute.set_user_attribute(user, REGISTRATION_AFFILIATE_ID, affiliate_id)


def _record_utm_registration_attribution(request, user):
    """
    Attribute this user's registration to the latest UTM referrer, if
    applicable.
    """
    utm_cookie_name = RegistrationCookieConfiguration.current().utm_cookie_name
    utm_cookie = request.COOKIES.get(utm_cookie_name)
    if user and utm_cookie:
        utm = json.loads(utm_cookie)
        for utm_parameter_name in REGISTRATION_UTM_PARAMETERS:
            utm_parameter = utm.get(utm_parameter_name)
            if utm_parameter:
                UserAttribute.set_user_attribute(
                    user,
                    REGISTRATION_UTM_PARAMETERS.get(utm_parameter_name),
                    utm_parameter
                )
        created_at_unixtime = utm.get('created_at')
        if created_at_unixtime:
            # We divide by 1000 here because the javascript timestamp generated is in milliseconds not seconds.
            # PYTHON: time.time()      => 1475590280.823698
            # JS: new Date().getTime() => 1475590280823
            created_at_datetime = datetime.datetime.fromtimestamp(int(created_at_unixtime) / float(1000), tz=UTC)
            UserAttribute.set_user_attribute(
                user,
                REGISTRATION_UTM_CREATED_AT,
                created_at_datetime
            )


class RegistrationView(APIView):
    # pylint: disable=missing-docstring
    """HTTP end-points for creating a new user. """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(transaction.non_atomic_requests)
    @method_decorator(sensitive_post_parameters("password"))
    def dispatch(self, request, *args, **kwargs):
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return HttpResponse(RegistrationFormFactory().get_registration_form(request).to_json(),
                            content_type="application/json")

    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create the user's account.

        You must send all required form fields with the request.

        You can optionally send a "course_id" param to indicate in analytics
        events that the user registered while enrolling in a particular course.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists
            HttpResponse: 403 operation not allowed
        """
        data = request.POST.copy()
        self._handle_terms_of_service(data)

        response = self._handle_duplicate_email_username(request, data)
        if response:
            return response

        response, user = self._create_account(request, data)
        if response:
            return response

        redirect_url = get_next_url_for_login_page(request, include_host=True)
        response = self._create_response(request, {}, status_code=200, redirect_url=redirect_url)
        set_logged_in_cookies(request, response, user)
        return response

    def _handle_duplicate_email_username(self, request, data):
        # pylint: disable=no-member
        # TODO Verify whether this check is needed here - it may be duplicated in user_api.
        email = data.get('email')
        username = data.get('username')
        errors = {}

        if email is not None and email_exists_or_retired(email):
            errors["email"] = [{"user_message": accounts_settings.EMAIL_CONFLICT_MSG.format(email_address=email)}]

        if username is not None and username_exists_or_retired(username):
            errors["username"] = [{"user_message": accounts_settings.USERNAME_CONFLICT_MSG.format(username=username)}]

        if errors:
            return self._create_response(request, errors, status_code=409)

    def _handle_terms_of_service(self, data):
        # Backwards compatibility: the student view expects both
        # terms of service and honor code values.  Since we're combining
        # these into a single checkbox, the only value we may get
        # from the new view is "honor_code".
        # Longer term, we will need to make this more flexible to support
        # open source installations that may have separate checkboxes
        # for TOS, privacy policy, etc.
        if data.get("honor_code") and "terms_of_service" not in data:
            data["terms_of_service"] = data["honor_code"]

    def _create_account(self, request, data):
        response, user = None, None
        try:
            user = create_account_with_params(request, data)
        except AccountValidationError as err:
            errors = {
                err.field: [{"user_message": text_type(err)}]
            }
            response = self._create_response(request, errors, status_code=409)
        except ValidationError as err:
            # Should only get field errors from this exception
            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            errors = {
                field: [{"user_message": error} for error in error_list]
                for field, error_list in err.message_dict.items()
            }
            response = self._create_response(request, errors, status_code=400)
        except PermissionDenied:
            response = HttpResponseForbidden(_("Account creation not allowed."))

        return response, user

    def _create_response(self, request, response_dict, status_code, redirect_url=None):
        if status_code == 200:
            # keeping this `success` field in for now, as we have outstanding clients expecting this
            response_dict['success'] = True
        else:
            self._log_validation_errors(request, response_dict, status_code)
        if redirect_url:
            response_dict['redirect_url'] = redirect_url
        return JsonResponse(response_dict, status=status_code)

    def _log_validation_errors(self, request, errors, status_code):
        if not REGISTRATION_FAILURE_LOGGING_FLAG.is_enabled():
            return

        try:
            for field_key, errors in errors.items():
                for error in errors:
                    log.info(
                        'message=registration_failed, status_code=%d, agent="%s", field="%s", error="%s"',
                        status_code,
                        request.META.get('HTTP_USER_AGENT', ''),
                        field_key,
                        error['user_message']
                    )
        except:  # pylint: disable=bare-except
            log.exception("Failed to log registration validation error")
            pass


# pylint: disable=line-too-long
class RegistrationValidationView(APIView):
    """
        **Use Cases**

            Get validation information about user data during registration.
            Client-side may request validation for any number of form fields,
            and the API will return a conclusion from its analysis for each
            input (i.e. valid or not valid, or a custom, detailed message).

        **Example Requests and Responses**

            - Checks the validity of the username and email inputs separately.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "hi_im_new",
            >>>     "email": "newguy101@edx.org"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "email": ""
            >>>     }
            >>> }
            Empty strings indicate that there was no problem with the input.

            - Checks the validity of the password field (its validity depends
              upon both the username and password fields, so we need both). If
              only password is input, we don't check for password/username
              compatibility issues.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "myname",
            >>>     "password": "myname"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "password": "Password cannot be the same as the username."
            >>>     }
            >>> }

            - Checks the validity of the username, email, and password fields
              separately, and also tells whether an account exists. The password
              field's validity depends upon both the username and password, and
              the account's existence depends upon both the username and email.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "hi_im_new",
            >>>     "email": "cto@edx.org",
            >>>     "password": "p"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "email": "It looks like cto@edx.org belongs to an existing account. Try again with a different email address.",
            >>>         "password": "Password must be at least 2 characters long",
            >>>     }
            >>> }
            In this example, username is valid and (we assume) there is
            a preexisting account with that email. The password also seems
            to contain the username.

            Note that a validation decision is returned *for all* inputs, whether
            positive or negative.

        **Available Handlers**

            "name":
                A handler to check the validity of the user's real name.
            "username":
                A handler to check the validity of usernames.
            "email":
                A handler to check the validity of emails.
            "confirm_email":
                A handler to check whether the confirmation email field matches
                the email field.
            "password":
                A handler to check the validity of passwords; a compatibility
                decision with the username is made if it exists in the input.
            "country":
                A handler to check whether the validity of country fields.
    """

    # This end-point is available to anonymous users, so no authentication is needed.
    authentication_classes = []

    def name_handler(self, request):
        name = request.data.get('name')
        return get_name_validation_error(name)

    def username_handler(self, request):
        """ Validates whether the username is valid. """
        username = request.data.get('username')
        invalid_username_error = get_username_validation_error(username)
        username_exists_error = get_username_existence_validation_error(username)
        # We prefer seeing for invalidity first.
        # Some invalid usernames (like for superusers) may exist.
        return invalid_username_error or username_exists_error

    def email_handler(self, request):
        """ Validates whether the email address is valid. """
        email = request.data.get('email')
        invalid_email_error = get_email_validation_error(email)
        email_exists_error = get_email_existence_validation_error(email)
        # We prefer seeing for invalidity first.
        # Some invalid emails (like a blank one for superusers) may exist.
        return invalid_email_error or email_exists_error

    def confirm_email_handler(self, request):
        email = request.data.get('email')
        confirm_email = request.data.get('confirm_email')
        return get_confirm_email_validation_error(confirm_email, email)

    def password_handler(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        return get_password_validation_error(password, username, email)

    def country_handler(self, request):
        country = request.data.get('country')
        return get_country_validation_error(country)

    validation_handlers = {
        "name": name_handler,
        "username": username_handler,
        "email": email_handler,
        "confirm_email": confirm_email_handler,
        "password": password_handler,
        "country": country_handler
    }

    @method_decorator(
        ratelimit(key=REAL_IP_KEY, rate=settings.REGISTRATION_VALIDATION_RATELIMIT, method='POST', block=True)
    )
    def post(self, request):
        """
        POST /api/user/v1/validation/registration/

        Expects request of the form
        ```
        {
            "name": "Dan the Validator",
            "username": "mslm",
            "email": "mslm@gmail.com",
            "confirm_email": "mslm@gmail.com",
            "password": "password123",
            "country": "PK"
        }
        ```
        where each key is the appropriate form field name and the value is
        user input. One may enter individual inputs if needed. Some inputs
        can get extra verification checks if entered along with others,
        like when the password may not equal the username.
        """
        validation_decisions = {}
        for form_field_key in self.validation_handlers:
            # For every field requiring validation from the client,
            # request a decision for it from the appropriate handler.
            if form_field_key in request.data:
                handler = self.validation_handlers[form_field_key]
                validation_decisions.update({
                    form_field_key: handler(self, request)
                })
        return Response({"validation_decisions": validation_decisions})
