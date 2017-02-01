"""
This file contains celery tasks for email marketing signal handler.
"""
import logging
import time
from datetime import datetime, timedelta

from celery import task
from django.core.cache import cache
from django.conf import settings

from email_marketing.models import EmailMarketingConfiguration
from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)
SAILTHRU_LIST_CACHE_KEY = "email.marketing.cache"


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user(self, sailthru_vars, email, site=None, new_user=False, activation=False):
    """
    Adds/updates Sailthru profile information for a user.
     Args:
        sailthru_vars(dict): User profile information to pass as 'vars' to Sailthru
        email(str): User email address
        new_user(boolean): True if new registration
        activation(boolean): True if activation request
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
    try:
        sailthru_response = sailthru_client.api_post("user",
                                                     _create_email_user_param(sailthru_vars, sailthru_client,
                                                                              email, new_user, email_config,
                                                                              site=site))

    except SailthruClientError as exc:
        log.error("Exception attempting to add/update user %s in Sailthru - %s", email, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error("Error attempting to add/update user in Sailthru: %s", error.get_message())
        if _retryable_sailthru_error(error):
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)
        return

    # if activating user, send welcome email
    if activation and email_config.sailthru_activation_template:
        scheduled_datetime = datetime.utcnow() + timedelta(seconds=email_config.welcome_email_send_delay)
        try:
            sailthru_response = sailthru_client.api_post(
                "send",
                {
                    "email": email,
                    "template": email_config.sailthru_activation_template,
                    "schedule_time": scheduled_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            )
        except SailthruClientError as exc:
            log.error("Exception attempting to send welcome email to user %s in Sailthru - %s", email, unicode(exc))
            raise self.retry(exc=exc,
                             countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)

        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error("Error attempting to send welcome email to user in Sailthru: %s", error.get_message())
            if _retryable_sailthru_error(error):
                raise self.retry(countdown=email_config.sailthru_retry_interval,
                                 max_retries=email_config.sailthru_max_retries)


# pylint: disable=not-callable
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
        log.error("Exception attempting to update email for %s in Sailthru - %s", old_email, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error("Error attempting to update user email address in Sailthru: %s", error.get_message())
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
    if site and site.get('id') != settings.SITE_ID:
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
        log.error("Exception attempting to get list from Sailthru - %s", unicode(exc))
        return {}

    if not sailthru_get_response.is_ok():
        error = sailthru_get_response.get_error()
        log.info("Error attempting to read list record from Sailthru: %s", error.get_message())
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
        log.error("Exception attempting to list record for key %s in Sailthru - %s", list_name, unicode(exc))
        return False

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error("Error attempting to create list in Sailthru: %s", error.get_message())
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
