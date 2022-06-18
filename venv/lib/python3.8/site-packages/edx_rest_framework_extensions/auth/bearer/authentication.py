""" Bearer Authentication class. """

import logging

import requests
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_custom_attribute
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from edx_rest_framework_extensions.exceptions import UserInfoRetrievalFailed
from edx_rest_framework_extensions.settings import get_setting


logger = logging.getLogger(__name__)


class BearerAuthentication(BaseAuthentication):
    """
    Simple token based authentication.

    This authentication class is useful for authenticating an OAuth2 access token against a remote
    authentication provider. Clients should authenticate by passing the token key in the "Authorization" HTTP header,
    prepended with the string `"Bearer "`.

    This class relies on the OAUTH2_USER_INFO_URL being set to the value of an endpoint on the OAuth provider, that
    returns a JSON object with information about the user. See ``process_user_info_response`` for the expected format
    of this object. This data will be used to get, or create, a ``User``. Additionally, it is assumed that a successful
    response from this endpoint (authenticated with the provided access token) implies the access token is valid.

    Example Header:
        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    def get_user_info_url(self):
        """ Returns the URL, hosted by the OAuth2 provider, from which user information can be pulled. """
        return get_setting('OAUTH2_USER_INFO_URL')

    def authenticate(self, request):
        set_custom_attribute("BearerAuthentication", "Failed")  # default value
        if not self.get_user_info_url():
            logger.warning('The setting OAUTH2_USER_INFO_URL is invalid!')
            set_custom_attribute("BearerAuthentication", "NoURL")
            return None
        set_custom_attribute("BearerAuthentication_user_info_url", self.get_user_info_url())
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'bearer':
            set_custom_attribute("BearerAuthentication", "None")
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        if len(auth) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        output = self.authenticate_credentials(auth[1].decode('utf8'))
        set_custom_attribute("BearerAuthentication", "Success")
        return output

    def authenticate_credentials(self, token):
        """
        Validate the bearer token against the OAuth provider.

        Arguments:
            token (str): Access token to validate

        Returns:
            (tuple): tuple containing:

                user (User): User associated with the access token
                access_token (str): Access token

        Raises:
            AuthenticationFailed: The user is inactive, or retrieval of user info failed.
        """

        try:
            user_info = self.get_user_info(token)
        except UserInfoRetrievalFailed as authentication_error:
            msg = 'Failed to retrieve user info. Unable to authenticate.'
            logger.error(msg)
            raise exceptions.AuthenticationFailed(msg) from authentication_error

        user, __ = get_user_model().objects.get_or_create(username=user_info['username'], defaults=user_info)

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')

        return user, token

    def get_user_info(self, token):
        """
        Retrieves the user info from the OAuth provider.

        Arguments:
            token (str): OAuth2 access token.

        Returns:
            dict

        Raises:
            UserInfoRetrievalFailed: Retrieval of user info from the remote server failed.
        """

        url = self.get_user_info_url()

        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(url, headers=headers)
        except requests.RequestException as error:
            logger.exception('Failed to retrieve user info due to a request exception.')
            raise UserInfoRetrievalFailed from error

        if response.status_code == 200:
            return self.process_user_info_response(response.json())
        else:
            msg = 'Failed to retrieve user info. Server [{server}] responded with status [{status}].'.format(
                server=url,
                status=response.status_code
            )
            raise UserInfoRetrievalFailed(msg)

    def process_user_info_response(self, response):
        """
        Process the user info response data.

        By default, this simply maps the edX user info key-values (example below) to Django-friendly names. If your
        provider returns different fields, you should sub-class this class and override this method.

        .. code-block:: python

            {
                "username": "jdoe",
                "email": "jdoe@example.com",
                "first_name": "Jane",
                "last_name": "Doe"
            }

        Arguments:
            response (dict): User info data

        Returns:
            dict
        """
        mapping = (
            ('username', 'preferred_username'),
            ('email', 'email'),
            ('last_name', 'family_name'),
            ('first_name', 'given_name'),
        )

        return {dest: response[source] for dest, source in mapping}

    def authenticate_header(self, request):
        return 'Bearer'
