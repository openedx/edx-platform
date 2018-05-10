"""Helper functions for working with Credentials."""
from __future__ import unicode_literals

from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.token_utils import JwtBuilder


def get_credentials_api_client(user):
    """ Returns an authenticated Credentials API client. """

    scopes = ['email', 'profile']
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    jwt = JwtBuilder(user).build_token(scopes, expires_in)
    return EdxRestApiClient(CredentialsApiConfig.current().internal_api_url, jwt=jwt)


def get_credentials(user, program_uuid=None):
    """
    Given a user, get credentials earned from the credentials service.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.

    Keyword Arguments:
        program_uuid (str): UUID of the program whose credential to retrieve.

    Returns:
        list of dict, representing credentials returned by the Credentials
        service.
    """
    credential_configuration = CredentialsApiConfig.current()

    querystring = {'username': user.username, 'status': 'awarded'}

    if program_uuid:
        querystring['program_uuid'] = program_uuid

    # Bypass caching for staff users, who may be generating credentials and
    # want to see them displayed immediately.
    use_cache = credential_configuration.is_cache_enabled and not user.is_staff
    cache_key = credential_configuration.CACHE_KEY + '.' + user.username if use_cache else None
    api = get_credentials_api_client(user)

    return get_edx_api_data(
        credential_configuration, 'credentials', api=api, querystring=querystring, cache_key=cache_key
    )
