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
from sailthru.sailthru_error import SailthruClientError
from six import text_type

from common.djangoapps import third_party_auth
from common.djangoapps.course_modes.models import CourseMode
from edx_toggles.toggles import WaffleSwitchNamespace
from lms.djangoapps.email_marketing.tasks import (
    get_email_cookies_via_sailthru,
    update_course_enrollment,
    update_user,
    update_user_email
)
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_authn.cookies import CREATE_LOGON_COOKIE
from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER
from common.djangoapps.student.signals import SAILTHRU_AUDIT_PURCHASE
from common.djangoapps.util.model_utils import USER_FIELD_CHANGED

from .models import EmailMarketingConfiguration

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country', LANGUAGE_KEY]

WAFFLE_NAMESPACE = 'sailthru'
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

SAILTHRU_AUDIT_PURCHASE_ENABLED = 'audit_purchase_enabled'


@receiver(SAILTHRU_AUDIT_PURCHASE)
def update_sailthru(sender, user, mode, course_id, **kwargs):  # pylint: disable=unused-argument
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
        email = user.email.encode('utf-8')
        update_course_enrollment.delay(email, course_id, mode, site=_get_current_site())


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
        log.error(u"Timeout error while attempting to obtain cookie from Sailthru: %s", text_type(exc))
        return response
    except SailthruClientError as exc:
        log.error(u"Exception attempting to obtain cookie from Sailthru: %s", text_type(exc))
        return response
    except Exception:
        log.error(u"Exception Connecting to celery task for %s", user.email)
        return response

    if not cookie:
        log.error(u"No cookie returned attempting to obtain cookie from Sailthru for %s", user.email)
        return response
    else:
        response.set_cookie(
            'sailthru_hid',
            cookie,
            max_age=365 * 24 * 60 * 60,  # set for 1 year
            domain=settings.SESSION_COOKIE_DOMAIN,
            path='/',
            secure=request.is_secure()
        )
        log.info(u"sailthru_hid cookie:%s successfully retrieved for user %s", cookie, user.email)

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

    log.info(u"Started at %s and ended at %s, time spent:%s milliseconds",
             time_before_call.isoformat(' '),
             time_after_call.isoformat(' '),
             delta_sailthru_api_call_time.microseconds / 1000)
