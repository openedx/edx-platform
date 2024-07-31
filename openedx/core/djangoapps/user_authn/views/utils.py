"""
User Auth Views Utils
"""
import logging
import re
import json

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from ipware.ip import get_client_ip
from text_unidecode import unidecode
from django.dispatch import Signal

from common.djangoapps.third_party_auth.saml import SAP_SUCCESSFACTORS_SAML_KEY
from openedx.core.djangoapps.user_authn.tasks import check_pwned_password_and_send_track_event
from common.djangoapps.student.models import (
    RegistrationCookieConfiguration,
    create_comments_service_user,
)
from lms.djangoapps.discussion.notification_prefs.views import enable_notifications
from common.djangoapps import third_party_auth
from common.djangoapps.student.helpers import (
    create_or_set_user_attribute_created_on_site,
    get_next_url_for_login_page,
    get_redirect_url_with_host
)
from common.djangoapps.track import segment
from common.djangoapps.third_party_auth import pipeline
from common.djangoapps.third_party_auth.models import clean_username
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip
from common.djangoapps.student.models import UserAttribute
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx_events.learning.signals import STUDENT_REGISTRATION_COMPLETED
from openedx_events.learning.data import UserData, UserPersonalData

import random
import string
from pytz import UTC
import datetime

log = logging.getLogger(__name__)
AUDIT_LOG = logging.getLogger("audit")
API_V1 = 'v1'
UUID4_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
ENTERPRISE_ENROLLMENT_URL_REGEX = fr'/enterprise/{UUID4_REGEX}/course/{settings.COURSE_KEY_REGEX}/enroll'
IS_MARKETABLE = 'is_marketable'
REGISTER_USER = Signal()

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


def third_party_auth_context(request, redirect_to, tpa_hint=None):
    """
    Context for third party auth providers and the currently running pipeline.

    Arguments:
        request (HttpRequest): The request, used to determine if a pipeline
            is currently running.
        redirect_to: The URL to send the user to following successful
            authentication.
        tpa_hint (string): An override flag that will return a matching provider
            as long as its configuration has been enabled

    Returns:
        dict

    """
    context = {
        "currentProvider": None,
        "platformName": configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        "providers": [],
        "secondaryProviders": [],
        "finishAuthUrl": None,
        "errorMessage": None,
        "registerFormSubmitButtonText": _("Create Account"),
        "syncLearnerProfileData": False,
        "pipeline_user_details": {}
    }

    if third_party_auth.is_enabled():
        for enabled in third_party_auth.provider.Registry.displayed_for_login(tpa_hint=tpa_hint):
            info = {
                "id": enabled.provider_id,
                "name": enabled.name,
                "iconClass": enabled.icon_class or None,
                "iconImage": enabled.icon_image.url if enabled.icon_image else None,
                "skipHintedLogin": enabled.skip_hinted_login_dialog,
                "skipRegistrationForm": enabled.skip_registration_form,
                "loginUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_LOGIN,
                    redirect_url=redirect_to,
                ),
                "registerUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_REGISTER,
                    redirect_url=redirect_to,
                ),
            }
            context["providers" if not enabled.secondary else "secondaryProviders"].append(info)

        running_pipeline = pipeline.get(request)
        if running_pipeline is not None:
            current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)
            user_details = running_pipeline['kwargs']['details']
            if user_details:
                username = running_pipeline['kwargs'].get('username') or user_details.get('username')
                if username:
                    user_details['username'] = clean_username(username)
                context['pipeline_user_details'] = user_details

            if current_provider is not None:
                context["currentProvider"] = current_provider.name
                context["finishAuthUrl"] = pipeline.get_complete_url(current_provider.backend_name)
                context["syncLearnerProfileData"] = current_provider.sync_learner_profile_data

                if current_provider.skip_registration_form:
                    # As a reliable way of "skipping" the registration form, we just submit it automatically
                    context["autoSubmitRegForm"] = True

        # Check for any error messages we may want to display:
        for msg in messages.get_messages(request):
            if msg.extra_tags.split()[0] == "social-auth":
                # msg may or may not be translated. Try translating [again] in case we are able to:
                context["errorMessage"] = _(str(msg))  # pylint: disable=E7610
                break

    return context


def get_mfe_context(request, redirect_to, tpa_hint=None):
    """
    Returns Authn MFE context.
    """

    ip_address = get_client_ip(request)[0]
    country_code = country_code_from_ip(ip_address)
    context = third_party_auth_context(request, redirect_to, tpa_hint)
    context.update({
        'countryCode': country_code,
    })
    return context


def _get_username_prefix(data):
    """
    Get the username prefix (name initials) based on the provided data.

    Args:
    - data (dict):  Registration payload.

    Returns:
    - str: Name initials or None.
    """
    username_regex_partial = settings.USERNAME_REGEX_PARTIAL
    valid_username_regex = r'^[A-Za-z0-9_\-]+$'
    full_name = ''
    try:
        if data.get('first_name', '').strip() and data.get('last_name', '').strip():
            full_name = f"{unidecode(data.get('first_name', ''))} {unidecode(data.get('last_name', ''))}"
        elif data.get('name', '').strip():
            full_name = unidecode(data['name'])

        if full_name.strip():
            matched_name = re.findall(username_regex_partial, full_name)
            if matched_name:
                full_name = " ".join(matched_name)
                name_initials = "".join([name_part[0] for name_part in full_name.split()[:2]])
                if re.match(valid_username_regex, name_initials):
                    return name_initials.upper() if name_initials else None

    except Exception as e:  # pylint: disable=broad-except
        logging.info(f"Error in _get_username_prefix: {e}")
        return None

    return None


def get_auto_generated_username(data):
    """
    Generate username based on learner's name initials, current date and configurable random string.

    This function creates a username in the format <name_initials>_<YYMM>_<configurable_random_string>

    The length of random string is determined by AUTO_GENERATED_USERNAME_RANDOM_STRING_LENGTH setting.

     Args:
    - data (dict):  Registration payload.

    Returns:
    - str: username.
    """
    current_year, current_month = datetime.datetime.now().strftime('%y %m').split()

    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.digits,
        k=settings.AUTO_GENERATED_USERNAME_RANDOM_STRING_LENGTH))

    username_prefix = _get_username_prefix(data)
    username_suffix = f"{current_year}{current_month}_{random_string}"

    # We generate the username regardless of whether the name is empty or invalid. We do this
    # because the name validations occur later, ensuring that users cannot create an account without a valid name.
    return f"{username_prefix}_{username_suffix}" if username_prefix else username_suffix


def complete_user_registration(
    user, profile, params, third_party_provider, registration, is_marketable, request, running_pipeline, cleaned_password
):
    from openedx.features.enterprise_support.utils import is_enterprise_learner
    from common.djangoapps.student.models import Registration
    print(f'\n\n\n\n\ncomplete_user_registration user={user} profile={profile} params={params} id={user.id} third_party_provider={third_party_provider} registration={registration} is_marketable={is_marketable} running_pipeline={running_pipeline} cleaned_password={cleaned_password} request.COOKIES={request.COOKIES} request.site={request.site} \n\n\n\n\n\n\n\n\n\n')
    try:
        _record_is_marketable_attribute(is_marketable, user)
    # Don't prevent a user from registering if is_marketable is not being set.
    # Also update the is_marketable value to None so that it is consistent with
    # our database when we send it to segment.
    except Exception:  # pylint: disable=broad-except
        log.exception('Error while setting is_marketable attribute.')
        is_marketable = None

    _track_user_registration(user, profile, params, third_party_provider, registration, is_marketable)

    # Sites using multiple languages need to record the language used during registration.
    # If not, compose_and_send_activation_email will be sent in site's default language only.
    print(f'\n\n\n\n create_or_set_user_attribute_created_on_site user={user} request.site={request.site}')
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
        from common.djangoapps.student.views.management import compose_and_send_activation_email

        redirect_to, root_url = get_next_url_for_login_page(request, include_host=True)
        redirect_url = get_redirect_url_with_host(root_url, redirect_to)
        compose_and_send_activation_email(user, profile, registration, redirect_url, True)

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception(f"Enable discussion notifications failed for user {user.id}.")

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)

    # .. event_implemented_name: STUDENT_REGISTRATION_COMPLETED
    STUDENT_REGISTRATION_COMPLETED.send_event(
        user=UserData(
            pii=UserPersonalData(
                username=user.username,
                email=user.email,
                name=user.profile.name,
            ),
            id=user.id,
            is_active=user.is_active,
        ),
    )

    create_comments_service_user(user)

    try:
        _record_registration_attributions(request, user)
    # Don't prevent a user from registering due to attribution errors.
    except Exception:  # pylint: disable=broad-except
        log.exception('Error while attributing cookies to user registration.')

    # TODO: there is no error checking here to see that the user actually logged in successfully,
    # and is not yet an active user.
    is_new_user(cleaned_password, user)
    return user


def is_new_user(password, user):
    if user is not None:
        AUDIT_LOG.info(f"Login success on new account creation - {user.username}")
        check_pwned_password_and_send_track_event.delay(
            user_id=user.id,
            password=password,
            internal_user=user.is_staff,
            is_new_user=True,
            request_page='registration'
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
    print(f'\n\n\n_skip_activation_email sso_pipeline_email={sso_pipeline_email} ')
    print(f'\n\n\n_skip_activation_email user.email={user.email} ')
    print(f'\n\n\n_skip_activation_email third_party_provider={third_party_provider} ')
    print(f'\n\n\n_skip_activation_email SAP_SUCCESSFACTORS_SAML_KEY={SAP_SUCCESSFACTORS_SAML_KEY} ')
    print(f'\n\n\n_skip_activation_email getattr(third_party_provider, "identity_provider_type", None)={getattr(third_party_provider, "identity_provider_type", None)} ')

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

    print(f'\n\n\n_skip_activation_email valid_email={valid_email} ')
    # print(f'\n\n\n_skip_activation_email third_party_provider.skip_email_verification={third_party_provider.skip_email_verification} ')

    # log the cases where skip activation email flag is set, but email validity check fails
    if third_party_provider and third_party_provider.skip_email_verification and not valid_email:
        log.info(
            '[skip_email_verification=True][user=%s][pipeline-email=%s][identity_provider=%s][provider_type=%s] '
            'Account activation email sent as user\'s system email differs from SSO email.',
            user.email,
            sso_pipeline_email,
            getattr(third_party_provider, "provider_id", None),
            getattr(third_party_provider, "identity_provider_type", None)
        )

    print(f'\n\n\n_skip_activation_email AUTOMATIC_AUTH_FOR_TESTING= ', settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'))

    print(f'\n\n\n_skip_activation_email return=', (
        settings.FEATURES.get('SKIP_EMAIL_VALIDATION', None) or
        settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING') or
        (third_party_provider and third_party_provider.skip_email_verification and valid_email)
    ))
    return (
        settings.FEATURES.get('SKIP_EMAIL_VALIDATION', None) or
        settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING') or
        (third_party_provider and third_party_provider.skip_email_verification and valid_email)
    )



def _record_is_marketable_attribute(is_marketable, user):
    """
    Attribute this user's registration based on form data
    """
    if settings.MARKETING_EMAILS_OPT_IN and user:
        UserAttribute.set_user_attribute(user, IS_MARKETABLE, str(is_marketable).lower())


def _track_user_registration(user, profile, params, third_party_provider, registration, is_marketable):
    print(f'\n\n\n _track_user_registration => user: {user} , profile: {profile} , params: {params} , third_party_provider: {third_party_provider} , registration: {registration} ,  is_marketable: {is_marketable}')
    """ Track the user's registration. """
    if True or hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
        traits = {
            'email': user.email,
            'username': user.username,
            'name': profile.name,
            # Mailchimp requires the age & yearOfBirth to be integers, we send a sane integer default if falsey.
            'age': profile.age or -1,
            'yearOfBirth': profile.year_of_birth or datetime.datetime.now(UTC).year,
            'education': profile.level_of_education_display,
            'address': profile.mailing_address,
            'gender': profile.gender_display,
            'country': str(profile.country),
            'is_marketable': is_marketable
        }
        if settings.MARKETING_EMAILS_OPT_IN and params.get('marketing_emails_opt_in'):
            email_subscribe = 'subscribed' if is_marketable else 'unsubscribed'
            traits['email_subscribe'] = email_subscribe

        # .. pii: Many pieces of PII are sent to Segment here. Retired directly through Segment API call in Tubular.
        # .. pii_types: email_address, username, name, birth_date, location, gender
        # .. pii_retirement: third_party
        segment.identify(user.id, traits)
        print('\n\n\n\n segment identify user: ', (
            user.id,
           traits,
        ), '\n\n\n\n')
        properties = {
            'category': 'conversion',
            # ..pii: Learner email is sent to Segment in following line and will be associated with analytics data.
            'email': user.email,
            'label': params.get('course_id'),
            'provider': third_party_provider.name if third_party_provider else None,
            'is_gender_selected': bool(profile.gender_display),
            'is_year_of_birth_selected': bool(profile.year_of_birth),
            'is_education_selected': bool(profile.level_of_education_display),
            'is_goal_set': bool(profile.goals),
            'total_registration_time': round(float(params.get('totalRegistrationTime', '0'))),
            'activation_key': registration.activation_key if registration else None,
            'host': params.get('host', ''),
            'app_name': params.get('app_name', ''),
            'utm_campaign': params.get('utm_campaign', ''),
        }
        # VAN-738 - added below properties to experiment marketing emails opt in/out events on Braze.
        if params.get('marketing_emails_opt_in') and settings.MARKETING_EMAILS_OPT_IN:
            properties['marketing_emails_opt_in'] = is_marketable

        # DENG-803: For segment events forwarded along to Hubspot, duplicate the `properties` section of
        # the event payload into the `traits` section so that they can be received. This is a temporary
        # fix until we implement this behavior outside of the LMS.
        # TODO: DENG-805: remove the properties duplication in the event traits.
        segment_traits = dict(properties)
        segment_traits['user_id'] = user.id
        segment_traits['joined_date'] = user.date_joined.strftime("%Y-%m-%d")
        print('\n\n\n\n segment event track: ', (
            user.id,
            "edx.bi.user.account.registered",
            properties,
            segment_traits,
        ), '\n\n\n\n')
        segment.track(
            user.id,
            "edx.bi.user.account.registered",
            properties=properties,
            traits=segment_traits,
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
