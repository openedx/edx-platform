"""
This module contains signals needed for email integration
"""
import datetime
import logging
from random import randint

import crum
from celery.exceptions import TimeoutError
from django.conf import settings
from django.dispatch import receiver
from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError
from six import text_type

import third_party_auth
from course_modes.models import CourseMode
from email_marketing.models import EmailMarketingConfiguration
from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_MAILINGS
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace
from lms.djangoapps.email_marketing.tasks import update_user, update_user_email, get_email_cookies_via_sailthru
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from student.cookies import CREATE_LOGON_COOKIE
from student.signals import ENROLL_STATUS_CHANGE
from student.views import REGISTER_USER
from util.model_utils import USER_FIELD_CHANGED
from .tasks import update_course_enrollment

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country', LANGUAGE_KEY]

WAFFLE_NAMESPACE = 'sailthru'
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

SAILTHRU_AUDIT_PURCHASE_ENABLED = 'audit_purchase_enabled'


@receiver(ENROLL_STATUS_CHANGE)
def update_sailthru(sender, event, user, mode, course_id, **kwargs):
    """
    Receives signal and calls a celery task to update the
    enrollment track
    Arguments:
        user: current user
        course_id: course key of a course
    Returns:
        None
    """
    if WAFFLE_SWITCHES.is_enabled(SAILTHRU_AUDIT_PURCHASE_ENABLED) and mode in CourseMode.AUDIT_MODES:
        course_key = str(course_id)
        email = str(user.email)
        update_course_enrollment.delay(email, course_key, mode)


@receiver(CREATE_LOGON_COOKIE)
def add_email_marketing_cookies(sender, response=None, user=None,
                                **kwargs):  # pylint: disable=unused-argument
    """
    Signal function for adding any cookies needed for email marketing

    Args:
        response: http response object
        user: The user object for the user being changed

    Returns:
        response: http response object with cookie added
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return response

    post_parms = {
        'id': user.email,
        'fields': {'keys': 1},
        'vars': {'last_login_date': datetime.datetime.now().strftime("%Y-%m-%d")}
    }

    # get anonymous_interest cookie to capture usage before logon
    request = crum.get_current_request()
    if request:
        sailthru_content = request.COOKIES.get('anonymous_interest')
        if sailthru_content:
            post_parms['cookies'] = {'anonymous_interest': sailthru_content}

    time_before_call = datetime.datetime.now()
    sailthru_response = get_email_cookies_via_sailthru.delay(user.email, post_parms)

    try:
        # synchronous call to get result of an asynchronous celery task, with timeout
        sailthru_response.get(timeout=email_config.user_registration_cookie_timeout_delay,
                              propagate=True)
        cookie = sailthru_response.result
        _log_sailthru_api_call_time(time_before_call)

    except TimeoutError as exc:
        log.error("Timeout error while attempting to obtain cookie from Sailthru: %s", text_type(exc))
        return response
    except SailthruClientError as exc:
        log.error("Exception attempting to obtain cookie from Sailthru: %s", text_type(exc))
        return response
    except Exception:
        log.error("Exception Connecting to celery task for %s", user.email)
        return response

    if not cookie:
        log.error("No cookie returned attempting to obtain cookie from Sailthru for %s", user.email)
        return response
    else:
        response.set_cookie(
            'sailthru_hid',
            cookie,
            max_age=365 * 24 * 60 * 60,  # set for 1 year
            domain=settings.SESSION_COOKIE_DOMAIN,
            path='/',
        )
        log.info("sailthru_hid cookie:%s successfully retrieved for user %s", cookie, user.email)

    return response


@receiver(REGISTER_USER)
def email_marketing_register_user(sender, user, registration,
                                  **kwargs):  # pylint: disable=unused-argument
    """
    Called after user created and saved

    Args:
        sender: Not used
        user: The user object for the user being changed
        registration: The user registration profile to activate user account
        kwargs: Not used
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore anonymous users
    if user.is_anonymous:
        return

    # perform update asynchronously
    update_user.delay(_create_sailthru_user_vars(user, user.profile, registration=registration), user.email,
                      site=_get_current_site(), new_user=True)


@receiver(USER_FIELD_CHANGED)
def email_marketing_user_field_changed(sender, user=None, table=None, setting=None,
                                       old_value=None, new_value=None,
                                       **kwargs):  # pylint: disable=unused-argument
    """
    Update a single user/profile field

    Args:
        sender: Not used
        user: The user object for the user being changed
        table: The name of the table being updated
        setting: The name of the setting being updated
        old_value: Prior value
        new_value: New value
        kwargs: Not used
    """

    # ignore anonymous users
    if user.is_anonymous:
        return

    # ignore anything but User, Profile or UserPreference tables
    if table not in {'auth_user', 'auth_userprofile', 'user_api_userpreference'}:
        return

    # ignore anything not in list of fields to handle
    if setting in CHANGED_FIELDNAMES:
        # skip if not enabled
        #  the check has to be here rather than at the start of the method to avoid
        #  accessing the config during migration 0001_date__add_ecommerce_service_user
        email_config = EmailMarketingConfiguration.current()
        if not email_config.enabled:
            return

        # Is the status of the user account changing to active?
        is_activation = (setting == 'is_active') and new_value is True

        # Is this change in the context of an SSO-initiated registration?
        third_party_provider = None
        if third_party_auth.is_enabled():
            running_pipeline = third_party_auth.pipeline.get(crum.get_current_request())
            if running_pipeline:
                third_party_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)

        # Send a welcome email if the user account is being activated
        # and we are not in a SSO registration flow whose associated
        # identity provider is configured to allow for the sending
        # of a welcome email.
        send_welcome_email = is_activation and (
            third_party_provider is None or third_party_provider.send_welcome_email
        )

        # set the activation flag when the user is marked as activated
        update_user.delay(_create_sailthru_user_vars(user, user.profile), user.email, site=_get_current_site(),
                          new_user=False, activation=send_welcome_email)

    elif setting == 'email':
        # email update is special case
        email_config = EmailMarketingConfiguration.current()
        if not email_config.enabled:
            return
        update_user_email.delay(user.email, old_value)


def _create_sailthru_user_vars(user, profile, registration=None):
    """
    Create sailthru user create/update vars from user + profile.
    """
    sailthru_vars = {'username': user.username,
                     'activated': int(user.is_active),
                     'joined_date': user.date_joined.strftime("%Y-%m-%d")}

    # Set the ui_lang to the User's prefered language, if specified. Otherwise use the application's default language.
    sailthru_vars['ui_lang'] = user.preferences.model.get_value(user, LANGUAGE_KEY, default=settings.LANGUAGE_CODE)

    if profile:
        sailthru_vars['fullname'] = profile.name
        sailthru_vars['gender'] = profile.gender
        sailthru_vars['education'] = profile.level_of_education

        if profile.year_of_birth:
            sailthru_vars['year_of_birth'] = profile.year_of_birth
        sailthru_vars['country'] = text_type(profile.country.code)

    if registration:
        sailthru_vars['activation_key'] = registration.activation_key
        sailthru_vars['signupNumber'] = randint(0, 9)

    return sailthru_vars


def _get_current_site():
    """
    Returns the site for the current request if any.
    """
    request = crum.get_current_request()
    if not request:
        return

    return {'id': request.site.id, 'domain': request.site.domain, 'name': request.site.name}


def _log_sailthru_api_call_time(time_before_call):
    """
    Logs Sailthru api synchronous call time
    """

    time_after_call = datetime.datetime.now()
    delta_sailthru_api_call_time = time_after_call - time_before_call

    log.info("Started at %s and ended at %s, time spent:%s milliseconds",
             time_before_call.isoformat(' '),
             time_after_call.isoformat(' '),
             delta_sailthru_api_call_time.microseconds / 1000)


@receiver(USER_RETIRE_MAILINGS)
def force_unsubscribe_all(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Synchronously(!) unsubscribes the given user from all Sailthru email lists.

    In the future this could be moved to a Celery task, however this is currently
    only used as part of user retirement, where we need a very reliable indication
    of success or failure.

    Args:
        email: Email address to unsubscribe
        new_email (optional): Email address to change 3rd party services to for this user (used in retirement to clear
                              personal information from the service)
    Returns:
        None
    """
    email = kwargs.get('email', None)
    new_email = kwargs.get('new_email', None)

    if not email:
        raise TypeError('Expected an email address to unsubscribe, but received None.')

    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    sailthru_parms = {
        "id": email,
        "optout_email": "all",
        "fields": {"optout_email": 1}
    }

    # If we have a new email address to change to, do that as well
    if new_email:
        sailthru_parms["keys"] = {
            "email": new_email
        }
        sailthru_parms["fields"]["keys"] = 1
        sailthru_parms["keysconflict"] = "merge"

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", sailthru_parms)
    except SailthruClientError as exc:
        error_msg = "Exception attempting to opt-out user {} from Sailthru - {}".format(email, text_type(exc))
        log.error(error_msg)
        raise Exception(error_msg)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        error_msg = "Error attempting to opt-out user {} from Sailthru - {}".format(email, error.get_message())
        log.error(error_msg)
        raise Exception(error_msg)
