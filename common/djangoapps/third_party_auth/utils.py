"""
Utility functions for third_party_auth
"""
from random import randint

from django.contrib.auth.models import User
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def user_exists(details):
    """
    Return True if user with given details exist in the system.

    Arguments:
        details (dict): dictionary containing user infor like email, username etc.

    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False


class UsernameGenerator(object):
    """Helper Class to generate a unique username using a basename."""

    def __init__(self, generator_settings=None):
        if not generator_settings:
            generator_settings = {}

        default_settings = {
            'SEPARATOR': '_',
            'LOWER': True,
            'RANDOM': False,
        }

        self.separator_character = generator_settings.get('SEPARATOR', default_settings['SEPARATOR'])
        self.in_lowercase = generator_settings.get('LOWER', default_settings['LOWER'])
        self.random = generator_settings.get('RANDOM', default_settings['RANDOM'])

    def replace_separator(self, basename):
        """
        Arguments:
            basename (str): string representing a basename for the user.

        Returns:
            (str): a new string with blank spaces  replaced by a custom separator.
        """
        username = basename.replace(' ', self.separator_character)
        return username

    def process_case(self, username):
        """
        Arguments:
            username (str): string representing a username for the user.

        Returns:
            (str): username in lower case if self.in_lowercase is True,
            otherwise returns the string unmodified.
        """
        if self.in_lowercase:
            return username.lower()
        else:
            return username

    def get_random_suffix(self):
        """
        Returns:
            (str): four digit random string.
        """
        random = "%04d" % randint(0, 9999)
        return random

    def generate_username(self, basename):
        """
        Arguments:
            basename (str): string representing a username for the user.

        Returns:
            (str): A unique username based on the provided string.
        """
        username = self.replace_separator(basename)
        initial_username = self.process_case(username)
        user_exists = User.objects.filter(username=initial_username).exists()

        if not user_exists:
            new_username = initial_username

        counter = 1
        while user_exists:
            if self.random:
                suffix = self.get_random_suffix()
            else:
                suffix = counter

            new_username = '{}{}{}'.format(initial_username, self.separator_character, suffix)
            user_exists = User.objects.filter(username=new_username).exists()
            counter += 1

        return new_username


def update_username_suggestion(details, provider_conf):
    """
    Arguments:
        provider_conf (dict): dictionary containing provider configuration info.

    Returns:
        (dict): user details dict with a username suggestion.
    """
    if configuration_helpers.get_value(
            'ENABLE_REGISTRATION_USERNAME_SUGGESTION',
            settings.FEATURES.get('ENABLE_REGISTRATION_USERNAME_SUGGESTION', False)):

        username_generator_settings = provider_conf.get('USERNAME_GENERATOR')
        username_base = details['username'] or details['fullname']
        username_generator = UsernameGenerator(username_generator_settings)
        username = username_generator.generate_username(username_base)
        details.update({'username': username})

    return details
