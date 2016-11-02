""" Course Discovery API Service. """
from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import JwtBuilder


def course_discovery_api_client(user):
    """ Returns a Course Discovery API client setup with authentication for the specified user. """
    scopes = ['email', 'profile']
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    jwt = JwtBuilder(user).build_token(scopes, expires_in)

    return EdxRestApiClient(settings.COURSE_CATALOG_API_URL, jwt=jwt)
