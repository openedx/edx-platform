"""
Utility methods for the account settings.
"""
import re
from urlparse import urlparse

from django.conf import settings
from django.utils.translation import ugettext as _


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
            ' Make sure that you are providing a valid username or a URL that contains "' +
            required_url_stub + '". To remove the link from your edX profile, leave this field blank.'
        ))


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
    return 'https://www.{}{}'.format(url_stub, username)


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
    username_match = re.search('(www\.)?' + url_stub + '(?P<username>.*?)[/]?$', url_domain_and_path, re.IGNORECASE)
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
