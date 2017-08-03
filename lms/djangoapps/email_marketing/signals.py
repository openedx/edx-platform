"""
This module contains signals needed for email integration
"""
import datetime
import logging

import crum
from django.conf import settings
from django.dispatch import receiver
from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError
from celery.exceptions import TimeoutError

from email_marketing.models import EmailMarketingConfiguration
from lms.djangoapps.email_marketing.tasks import update_user, update_user_email, get_email_cookies_via_sailthru
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from student.cookies import CREATE_LOGON_COOKIE
from student.views import REGISTER_USER
from util.model_utils import USER_FIELD_CHANGED

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country', LANGUAGE_KEY]


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
        log.error("Timeout error while attempting to obtain cookie from Sailthru: %s", unicode(exc))
        return response
    except SailthruClientError as exc:
        log.error("Exception attempting to obtain cookie from Sailthru: %s", unicode(exc))
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
def email_marketing_register_user(sender, user=None, profile=None,
                                  **kwargs):  # pylint: disable=unused-argument
    """
    Called after user created and saved

    Args:
        sender: Not used
        user: The user object for the user being changed
        profile: The user profile for the user being changed
        kwargs: Not used
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # perform update asynchronously
    update_user.delay(
        _create_sailthru_user_vars(user, user.profile), user.email, site=_get_current_site(), new_user=True
    )


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
    if user.is_anonymous():
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

        # perform update asynchronously
        update_user.delay(_create_sailthru_user_vars(user, user.profile), user.email, site=_get_current_site(),
                          new_user=False)

    elif setting == 'email':
        # email update is special case
        email_config = EmailMarketingConfiguration.current()
        if not email_config.enabled:
            return
        update_user_email.delay(user.email, old_value)


def _create_sailthru_user_vars(user, profile):
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
        sailthru_vars['country'] = unicode(profile.country.code)

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
