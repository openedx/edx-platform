"""
This module contains signals needed for email integration
"""
import crum
import datetime
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from student.models import ENROLL_STATUS_CHANGE
from student.cookies import CREATE_LOGON_COOKIE
from student.views import REGISTER_USER
from email_marketing.models import EmailMarketingConfiguration
from util.model_utils import USER_FIELD_CHANGED
from lms.djangoapps.email_marketing.tasks import (
    update_user, update_user_email, update_course_enrollment
)

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country']


@receiver(ENROLL_STATUS_CHANGE)
def handle_enroll_status_change(sender, event=None, user=None, mode=None, course_id=None,
                                **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for enroll/unenroll/purchase events
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled or not event or not user or not mode or not course_id:
        return

    # skip tracking (un)enrolls if simulated cost=0
    if email_config.sailthru_enroll_cost == 0:
        return

    request = crum.get_current_request()
    if not request:
        return

    # get string course_id serializable to send through celery
    course_id_string = unicode(course_id)

    # figure out course url
    course_url = _build_course_url(request, course_id_string, email_config)

    # pass event to email_marketing.tasks
    update_course_enrollment.delay(user.email, course_url, event, mode,
                                   course_id=course_id_string,
                                   message_id=request.COOKIES.get('sailthru_bid'))


def _build_course_url(request, course_id, email_config):
    """
    Build a course url from a course id and the host from the current request
    or use override in config
    :param request:
    :param course_id:
    :return:
    """
    path = reverse('info', kwargs={'course_id': course_id})
    if email_config.sailthru_lms_url_override:
        return '{}{}'.format(email_config.sailthru_lms_url_override, path)
    else:
        return '{}://{}{}'.format(request.scheme, request.get_host(), path)


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

    # get sailthru_content cookie to capture usage before logon
    request = crum.get_current_request()
    if request:
        sailthru_content = request.COOKIES.get('sailthru_content')
        if sailthru_content:
            post_parms['cookies'] = {'sailthru_content': sailthru_content}

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = \
            sailthru_client.api_post("user", post_parms)
    except SailthruClientError as exc:
        log.error("Exception attempting to obtain cookie from Sailthru: %s", unicode(exc))
        return response

    if sailthru_response.is_ok():
        if 'keys' in sailthru_response.json and 'cookie' in sailthru_response.json['keys']:
            cookie = sailthru_response.json['keys']['cookie']

            response.set_cookie(
                'sailthru_hid',
                cookie,
                max_age=365 * 24 * 60 * 60,  # set for 1 year
                domain=settings.SESSION_COOKIE_DOMAIN,
                path='/',
            )
        else:
            log.error("No cookie returned attempting to obtain cookie from Sailthru for %s", user.email)
    else:
        error = sailthru_response.get_error()
        # generally invalid email address
        log.info("Error attempting to obtain cookie from Sailthru: %s", error.get_message())
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
        update_user.delay(_create_sailthru_user_vars(user, user.profile), user.email, site=_get_current_site(),
                          new_user=False, activation=(setting == 'is_active') and new_value is True)

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
