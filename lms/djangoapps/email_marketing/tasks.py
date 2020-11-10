"""
This file contains celery tasks for email marketing signal handler.
"""


import logging
import time
from datetime import datetime, timedelta

import six
from celery import task
from django.conf import settings
from django.core.cache import cache
from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

from .models import EmailMarketingConfiguration

log = logging.getLogger(__name__)
SAILTHRU_LIST_CACHE_KEY = "email.marketing.cache"


@task(bind=True)
def get_email_cookies_via_sailthru(self, user_email, post_parms):
    """
    Adds/updates Sailthru cookie information for a new user.
     Args:
        post_parms(dict): User profile information to pass as 'vars' to Sailthru
    Returns:
        cookie(str): cookie fetched from Sailthru
    """

    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return None

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        log.info(
            u'Sending to Sailthru the user interest cookie [%s] for user [%s]',
            post_parms.get('cookies', ''),
            user_email
        )
        sailthru_response = sailthru_client.api_post("user", post_parms)
    except SailthruClientError as exc:
        log.error(u"Exception attempting to obtain cookie from Sailthru: %s", six.text_type(exc))
        raise SailthruClientError

    if sailthru_response.is_ok():
        if 'keys' in sailthru_response.json and 'cookie' in sailthru_response.json['keys']:
            cookie = sailthru_response.json['keys']['cookie']
            return cookie
        else:
            log.error(u"No cookie returned attempting to obtain cookie from Sailthru for %s", user_email)
    else:
        error = sailthru_response.get_error()
        # generally invalid email address
        log.info(u"Error attempting to obtain cookie from Sailthru: %s", error.get_message())

    return None


@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user(self, sailthru_vars, email, site=None, new_user=False, activation=False):
    """
    Adds/updates Sailthru profile information for a user.
     Args:
        sailthru_vars(dict): User profile information to pass as 'vars' to Sailthru
        email(str): User email address
        new_user(boolean): True if new registration
        activation(boolean): True if a welcome email should be sent
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # do not add user if registered at a white label site
    if not is_default_site(site):
        return

    sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
    try:
        sailthru_response = sailthru_client.api_post("user",
                                                     _create_email_user_param(sailthru_vars, sailthru_client,
                                                                              email, new_user, email_config,
                                                                              site=site))

    except SailthruClientError as exc:
        log.error(u"Exception attempting to add/update user %s in Sailthru - %s", email, six.text_type(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error(u"Error attempting to add/update user in Sailthru: %s", error.get_message())
        if _retryable_sailthru_error(error):
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)
        return

    if activation and email_config.sailthru_welcome_template and not sailthru_vars.get('is_enterprise_learner'):

        scheduled_datetime = datetime.utcnow() + timedelta(seconds=email_config.welcome_email_send_delay)
        try:
            sailthru_response = sailthru_client.api_post(
                "send",
                {
                    "email": email,
                    "template": email_config.sailthru_welcome_template,
                    "schedule_time": scheduled_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            )
        except SailthruClientError as exc:
            log.error(
                u"Exception attempting to send welcome email to user %s in Sailthru - %s",
                email,
                six.text_type(exc)
            )
            raise self.retry(exc=exc,
                             countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)

        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error(u"Error attempting to send welcome email to user in Sailthru: %s", error.get_message())
            if _retryable_sailthru_error(error):
                raise self.retry(countdown=email_config.sailthru_retry_interval,
                                 max_retries=email_config.sailthru_max_retries)


def is_default_site(site):
    """
    Checks whether the site is a default site or a white-label
    Args:
        site: A dict containing the site info
    Returns:
         Boolean
    """
    return not site or site.get('id') == settings.SITE_ID


@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user_email(self, new_email, old_email):
    """
    Adds/updates Sailthru when a user email address is changed
     Args:
        username(str): A string representation of user identifier
        old_email(str): Original email address
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore if email not changed
    if new_email == old_email:
        return

    sailthru_parms = {"id": old_email, "key": "email", "keysconflict": "merge", "keys": {"email": new_email}}

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", sailthru_parms)
    except SailthruClientError as exc:
        log.error(u"Exception attempting to update email for %s in Sailthru - %s", old_email, six.text_type(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error(u"Error attempting to update user email address in Sailthru: %s", error.get_message())
        if _retryable_sailthru_error(error):
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)


def _create_email_user_param(sailthru_vars, sailthru_client, email, new_user, email_config, site=None):
    """
    Create sailthru user create/update parms
    """
    sailthru_user = {'id': email, 'key': 'email'}
    sailthru_user['vars'] = dict(sailthru_vars, last_changed_time=int(time.time()))

    # if new user add to list
    if new_user:
        list_name = _get_or_create_user_list_for_site(
            sailthru_client, site=site, default_list_name=email_config.sailthru_new_user_list
        )
        sailthru_user['lists'] = {list_name: 1} if list_name else {email_config.sailthru_new_user_list: 1}

    return sailthru_user


def _get_or_create_user_list_for_site(sailthru_client, site=None, default_list_name=None):
    """
    Get the user list name from cache if exists else create one and return the name,
    callers of this function should perform the enabled check of email config.
    :param: sailthru_client
    :param: site
    :param: default_list_name
    :return: list name if exists or created else return None
    """
    if not is_default_site(site):
        list_name = site.get('domain', '').replace(".", "_") + "_user_list"
    else:
        list_name = default_list_name

    sailthru_list = _get_or_create_user_list(sailthru_client, list_name)
    return list_name if sailthru_list else default_list_name


def _get_or_create_user_list(sailthru_client, list_name):
    """
    Get list from sailthru and return if list_name exists else create a new one
    and return list data for all lists.
    :param sailthru_client
    :param list_name
    :return sailthru list
    """
    sailthru_list_cache = cache.get(SAILTHRU_LIST_CACHE_KEY)
    is_cache_updated = False
    if not sailthru_list_cache:
        sailthru_list_cache = _get_list_from_email_marketing_provider(sailthru_client)
        is_cache_updated = True

    sailthru_list = sailthru_list_cache.get(list_name)

    if not sailthru_list:
        is_created = _create_user_list(sailthru_client, list_name)
        if is_created:
            sailthru_list_cache = _get_list_from_email_marketing_provider(sailthru_client)
            is_cache_updated = True
            sailthru_list = sailthru_list_cache.get(list_name)

    if is_cache_updated:
        cache.set(SAILTHRU_LIST_CACHE_KEY, sailthru_list_cache)

    return sailthru_list


def _get_list_from_email_marketing_provider(sailthru_client):
    """
    Get sailthru list
    :param sailthru_client
    :return dict of sailthru lists mapped by list name
    """
    try:
        sailthru_get_response = sailthru_client.api_get("list", {})
    except SailthruClientError as exc:
        log.error(u"Exception attempting to get list from Sailthru - %s", six.text_type(exc))
        return {}

    if not sailthru_get_response.is_ok():
        error = sailthru_get_response.get_error()
        log.info(u"Error attempting to read list record from Sailthru: %s", error.get_message())
        return {}

    list_map = dict()
    for user_list in sailthru_get_response.json['lists']:
        list_map[user_list.get('name')] = user_list

    return list_map


def _create_user_list(sailthru_client, list_name):
    """
    Create list in Sailthru
    :param sailthru_client
    :param list_name
    :return boolean
    """
    list_params = {'list': list_name, 'primary': 0, 'public_name': list_name}
    try:
        sailthru_response = sailthru_client.api_post("list", list_params)
    except SailthruClientError as exc:
        log.error(u"Exception attempting to list record for key %s in Sailthru - %s", list_name, six.text_type(exc))
        return False

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error(u"Error attempting to create list in Sailthru: %s", error.get_message())
        return False

    return True


def _retryable_sailthru_error(error):
    """ Return True if error should be retried.

    9: Retryable internal error
    43: Rate limiting response
    others: Not retryable

    See: https://getstarted.sailthru.com/new-for-developers-overview/api/api-response-errors/
    """
    code = error.get_error_code()
    return code == 9 or code == 43


@task(bind=True)
def update_course_enrollment(self, email, course_key, mode, site=None):
    """Adds/updates Sailthru when a user adds to cart/purchases/upgrades a course
         Args:
            email: email address of enrolled user
            course_key: course key of course
            mode: mode user is enrolled in
            site: site where user enrolled
        Returns:
            None
    """
    # do not add user if registered at a white label site
    if not is_default_site(site):
        return

    course_url = build_course_url(course_key)
    config = EmailMarketingConfiguration.current()

    try:
        sailthru_client = SailthruClient(config.sailthru_key, config.sailthru_secret)
    except:
        return

    send_template = config.sailthru_enroll_template
    cost_in_cents = 0

    if not update_unenrolled_list(sailthru_client, email, course_url, False):
        schedule_retry(self, config)

    course_data = _get_course_content(course_key, course_url, sailthru_client, config)

    item = _build_purchase_item(course_key, course_url, cost_in_cents, mode, course_data)
    options = {}

    if send_template:
        options['send_template'] = send_template

    if not _record_purchase(sailthru_client, email, item, options):
        schedule_retry(self, config)


def build_course_url(course_key):
    """
    Generates and return url of the course info page by using course_key
    Arguments:
         course_key: course_key of the given course
    Returns
        a complete url of the course info page
    """
    return '{base_url}/courses/{course_key}/info'.format(base_url=settings.LMS_ROOT_URL,
                                                         course_key=six.text_type(course_key))


def update_unenrolled_list(sailthru_client, email, course_url, unenroll):
    """Maintain a list of courses the user has unenrolled from in the Sailthru user record
    Arguments:
        sailthru_client: SailthruClient
        email (str): user's email address
        course_url (str): LMS url for course info page.
        unenroll (boolean): True if unenrolling, False if enrolling
    Returns:
        False if retryable error, else True
    """
    try:
        # get the user 'vars' values from sailthru
        sailthru_response = sailthru_client.api_get("user", {"id": email, "fields": {"vars": 1}})
        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error(u"Error attempting to read user record from Sailthru: %s", error.get_message())
            return not _retryable_sailthru_error(error)

        response_json = sailthru_response.json

        unenroll_list = []
        if response_json and "vars" in response_json and response_json["vars"] \
           and "unenrolled" in response_json["vars"]:
            unenroll_list = response_json["vars"]["unenrolled"]

        changed = False
        # if unenrolling, add course to unenroll list
        if unenroll:
            if course_url not in unenroll_list:
                unenroll_list.append(course_url)
                changed = True

        # if enrolling, remove course from unenroll list
        elif course_url in unenroll_list:
            unenroll_list.remove(course_url)
            changed = True

        if changed:
            # write user record back
            sailthru_response = sailthru_client.api_post(
                'user', {'id': email, 'key': 'email', 'vars': {'unenrolled': unenroll_list}})

            if not sailthru_response.is_ok():
                error = sailthru_response.get_error()
                log.error(u"Error attempting to update user record in Sailthru: %s", error.get_message())
                return not _retryable_sailthru_error(error)

        return True

    except SailthruClientError as exc:
        log.exception(u"Exception attempting to update user record for %s in Sailthru - %s", email, six.text_type(exc))
        return False


def schedule_retry(self, config):
    """Schedule a retry"""
    raise self.retry(countdown=config.sailthru_retry_interval,
                     max_retries=config.sailthru_max_retries)


def _get_course_content(course_id, course_url, sailthru_client, config):
    """Get course information using the Sailthru content api or from cache.
        If there is an error, just return with an empty response.
        Arguments:
            course_id (str): course key of the course
            course_url (str): LMS url for course info page.
            sailthru_client : SailthruClient
            config : config options
        Returns:
            course information from Sailthru
        """
    # check cache first

    cache_key = "{}:{}".format(course_id, course_url)
    response = cache.get(cache_key)
    if not response:
        try:
            sailthru_response = sailthru_client.api_get("content", {"id": course_url})
            if not sailthru_response.is_ok():
                log.error('Could not get course data from Sailthru on enroll/unenroll event. ')
                response = {}
            else:
                response = sailthru_response.json
                cache.set(cache_key, response, config.sailthru_content_cache_age)

        except SailthruClientError:
            response = {}

    return response


def _build_purchase_item(course_id, course_url, cost_in_cents, mode, course_data):
    """Build and return Sailthru purchase item object"""

    # build item description
    item = {
        'id': "{}-{}".format(course_id, mode),
        'url': course_url,
        'price': cost_in_cents,
        'qty': 1,
    }

    # get title from course info if we don't already have it from Sailthru
    if 'title' in course_data:
        item['title'] = course_data['title']
    else:
        # can't find, just invent title
        item['title'] = u'Course {} mode: {}'.format(course_id, mode)

    if 'tags' in course_data:
        item['tags'] = course_data['tags']

    # add vars to item
    item['vars'] = dict(course_data.get('vars', {}), mode=mode, course_run_id=six.text_type(course_id))

    return item


def _record_purchase(sailthru_client, email, item, options):
    """
    Record a purchase in Sailthru
    Arguments:
        sailthru_client: SailthruClient
        email: user's email address
        item: Sailthru required information
        options: Sailthru purchase API options
    Returns:
        False if retryable error, else True
    """

    try:
        sailthru_response = sailthru_client.purchase(email, [item], options=options)

        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error(u"Error attempting to record purchase in Sailthru: %s", error.get_message())
            return not _retryable_sailthru_error(error)

    except SailthruClientError as exc:
        log.exception(u"Exception attempting to record purchase for %s in Sailthru - %s", email, six.text_type(exc))
        return False
    return True
