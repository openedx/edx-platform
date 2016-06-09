"""
This module contains signals needed for email integration
"""
import logging
import datetime

from django.dispatch import receiver

from student.models import UNENROLL_DONE
from student.cookies import CREATE_LOGON_COOKIE
from student.views import REGISTER_USER
from email_marketing.models import EmailMarketingConfiguration
from util.model_utils import USER_FIELD_CHANGED
from lms.djangoapps.email_marketing.tasks import update_user, update_user_email

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country']


@receiver(UNENROLL_DONE)
def handle_unenroll_done(sender, course_enrollment=None, skip_refund=False,
                         **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for unenrollments
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # TBD


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

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = \
            sailthru_client.api_post("user", {'id': user.email, 'fields': {'keys': 1},
                                              'vars': {'last_login_date':
                                                       datetime.datetime.now().strftime("%Y-%m-%d")}})
    except SailthruClientError as exc:
        log.error("Exception attempting to obtain cookie from Sailthru: %s", unicode(exc))
        return response

    if sailthru_response.is_ok():
        if 'keys' in sailthru_response.json and 'cookie' in sailthru_response.json['keys']:
            cookie = sailthru_response.json['keys']['cookie']

            response.set_cookie(
                'sailthru_hid',
                cookie,
                max_age=365 * 24 * 60 * 60  # set for 1 year
            )
        else:
            log.error("No cookie returned attempting to obtain cookie from Sailthru for %s", user.email)
    else:
        error = sailthru_response.get_error()
        log.error("Error attempting to obtain cookie from Sailthru: %s", error.get_message())
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
    log.info("Receiving REGISTER_USER")
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # perform update asynchronously
    update_user.delay(user.username, new_user=True)


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

    # ignore anything but User or Profile table
    if table != 'auth_user' and table != 'auth_userprofile':
        return

    # ignore anything not in list of fields to handle
    if setting in CHANGED_FIELDNAMES:
        # skip if not enabled
        #  the check has to be here rather than at the start of the method to avoid
        #  accessing the config during migration 0001_date__add_ecommerce_service_user
        email_config = EmailMarketingConfiguration.current()
        if not email_config.enabled:
            return
        # perform update asynchronously, flag if activation
        update_user.delay(user.username, new_user=False,
                          activation=(setting == 'is_active') and new_value is True)

    elif setting == 'email':
        # email update is special case
        email_config = EmailMarketingConfiguration.current()
        if not email_config.enabled:
            return
        update_user_email.delay(user.username, old_value)
