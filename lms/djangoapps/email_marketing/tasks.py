"""
This file contains celery tasks for email marketing signal handler.
"""
import logging
import datetime

from pytz import UTC

from celery import task
from django.contrib.auth.models import User

from student.models import UserProfile
from email_marketing.models import EmailMarketingConfiguration

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user(self, username):
    """
    Adds/updates Sailthru profile information for a user.
     Args:
        username(str): A string representation of user identifier
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.sailthru_enabled:
        return

    # get user
    user = User.objects.get(username=username)
    if not user:
        log.error("User not found duing Sailthru update %s", username)
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # get profile
    profile = UserProfile.objects.get(user=user)
    if not profile:
        log.error("User profile not found duing Sailthru update %s", username)
        return

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", _create_sailthru_user_parm(user, profile))
    except SailthruClientError as exc:
        log.error("Exception attempting to add/update user %s in Sailthru - %s", username, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        # put out error and schedule retry
        log.error("Error attempting to add/update user in Sailthru: %s", error.get_message())
        raise self.retry(countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user_email(self, username, old_email):
    """
    Adds/updates Sailthru when a user email address is changed
     Args:
        username(str): A string representation of user identifier
        old_email(str): Original email address
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.sailthru_enabled:
        return

    # get user
    user = User.objects.get(username=username)
    if not user:
        log.error("User not found duing Sailthru update %s", username)
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # ignore if email not changed
    if user.email == old_email:
        return

    sailthru_parms = {"id": old_email, "key": "email", "keysconflict": "merge", "keys": {"email": user.email}}

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", sailthru_parms)
    except SailthruClientError as exc:
        log.error("Exception attempting to update email for %s in Sailthru - %s", username, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error("Error attempting to update user email address in Sailthru: %s", error.get_message())
        raise self.retry(countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)


def _create_sailthru_user_parm(user, profile):
    """
    Create sailthru user create/update parms from user + profile.
    """
    sailthru_user = {'id': user.email, 'key': 'email'}
    sailthru_vars = {'username': user.username,
                     'activated': int(user.is_active),
                     'joined_date': user.date_joined.strftime("%Y-%m-%d")}
    sailthru_user['vars'] = sailthru_vars

    if profile:
        sailthru_vars['fullname'] = profile.name
        sailthru_vars['gender'] = profile.gender
        sailthru_vars['education'] = profile.level_of_education
        sailthru_vars['age'] = profile.age or -1
        sailthru_vars['yearOfBirth'] = profile.year_of_birth or datetime.datetime.now(UTC).year
        sailthru_vars['address'] = profile.mailing_address
        sailthru_vars['country'] = unicode(profile.country)

    return sailthru_user
