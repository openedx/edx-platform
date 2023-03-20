"""
Utility methods for the account settings.
"""

import logging
import random
import re
import string
from urllib.parse import urlparse  # pylint: disable=import-error

import waffle  # lint-amnesty, pylint: disable=invalid-django-waffle-import
from django.conf import settings
from django.utils.translation import gettext as _
from edx_django_utils.user import generate_password
from social_django.models import UserSocialAuth

from common.djangoapps.student.models import AccountRecovery, Registration, get_retired_email_by_email
from openedx.core.djangolib.oauth2_retirement_utils import retire_dot_oauth2_models

from ..models import UserRetirementStatus

ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH = 'enable_secondary_email_feature'
LOGGER = logging.getLogger(__name__)


def validate_social_link(platform_name, new_social_link):
    """
    Given a new social link for a user, ensure that the link takes one of the
    following forms:

    1) A valid url that comes from the correct social site.
    2) A valid username.
    3) A blank value.
    """
    formatted_social_link = format_social_link(platform_name, new_social_link)

    # Ensure that the new link is valid.
    if formatted_social_link is None:
        required_url_stub = settings.SOCIAL_PLATFORMS[platform_name]['url_stub']
        raise ValueError(_(
            'Make sure that you are providing a valid username or a URL that contains "{url_stub}". '
            'To remove the link from your {platform_name} profile, leave this field blank.'
        ).format(url_stub=required_url_stub, platform_name=settings.PLATFORM_NAME))


def format_social_link(platform_name, new_social_link):
    """
    Given a user's social link, returns a safe absolute url for the social link.

    Returns the following based on the provided new_social_link:
    1) Given an empty string, returns ''
    1) Given a valid username, return 'https://www.[platform_name_base][username]'
    2) Given a valid URL, return 'https://www.[platform_name_base][username]'
    3) Given anything unparseable, returns None
    """
    # Blank social links should return '' or None as was passed in.
    if not new_social_link:
        return new_social_link

    url_stub = settings.SOCIAL_PLATFORMS[platform_name]['url_stub']
    username = _get_username_from_social_link(platform_name, new_social_link)
    if not username:
        return None

    # For security purposes, always build up the url rather than using input from user.
    return f'https://www.{url_stub}{username}'


def _get_username_from_social_link(platform_name, new_social_link):
    """
    Returns the username given a social link.

    Uses the following logic to parse new_social_link into a username:
    1) If an empty string, returns it as the username.
    2) Given a URL, attempts to parse the username from the url and return it.
    3) Given a non-URL, returns the entire string as username if valid.
    4) If no valid username is found, returns None.
    """
    # Blank social links should return '' or None as was passed in.
    if not new_social_link:
        return new_social_link

    # Parse the social link as if it were a URL.
    parse_result = urlparse(new_social_link)
    url_domain_and_path = parse_result[1] + parse_result[2]
    url_stub = re.escape(settings.SOCIAL_PLATFORMS[platform_name]['url_stub'])
    username_match = re.search(r'(www\.)?' + url_stub + r'(?P<username>.*?)[/]?$', url_domain_and_path, re.IGNORECASE)
    if username_match:
        username = username_match.group('username')
    else:
        username = new_social_link

    # Ensure the username is a valid username.
    if not _is_valid_social_username(username):
        return None

    return username


def _is_valid_social_username(value):
    """
    Given a particular string, returns whether the string can be considered a safe username.
    This is a very liberal validation step, simply assuring forward slashes do not exist
    in the username.
    """
    return '/' not in value


def is_secondary_email_feature_enabled():
    """
    Checks to see if the django-waffle switch for enabling the secondary email feature is active

    Returns:
        Boolean value representing switch status
    """
    return waffle.switch_is_active(ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH)


def create_retirement_request_and_deactivate_account(user):
    """
    Adds user to retirement queue, unlinks social auth accounts, changes user passwords
    and delete tokens and activation keys
    """
    # Add user to retirement queue.
    UserRetirementStatus.create_retirement(user)

    # Unlink LMS social auth accounts
    UserSocialAuth.objects.filter(user_id=user.id).delete()

    # Change LMS password & email
    user.email = get_retired_email_by_email(user.email)
    user.set_unusable_password()
    user.save()

    # TODO: Unlink social accounts & change password on each IDA.
    # Remove the activation keys sent by email to the user for account activation.
    Registration.objects.filter(user=user).delete()

    # Delete OAuth tokens associated with the user.
    retire_dot_oauth2_models(user)
    AccountRecovery.retire_recovery_email(user.id)


def username_suffix_generator(suffix_length=4):
    """
    Generates a random, alternating number and letter string for the purpose of
    appending to non-unique usernames. Alternating is less likey to produce
    a significant/meaningful substring like an offensive word.
    """
    output = ''
    for i in range(suffix_length):
        if (i % 2) == 0:
            output += random.choice(string.ascii_lowercase)
        else:
            output += random.choice(string.digits)
    return output


def handle_retirement_cancellation(retirement, email_address=None):
    """
    Do the following in order to cancel retirement for a given user:

    1. Load the user record using the retired email address -and- change the email address back.
    2. Reset users password so they can request a password reset and log in again.
    3. No need to delete the accompanying "permanent" retirement request record - it gets done via Django signal.
    """
    retirement.user.email = email_address if email_address else retirement.original_email

    retirement.user.set_password(generate_password(length=25))
    retirement.user.save()

    retirement.delete()
