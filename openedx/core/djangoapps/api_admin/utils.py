""" Course Discovery API Service. """
from edx_rest_api_client.client import EdxRestApiClient
from openedx.core.lib.token_utils import get_id_token
from provider.oauth2.models import Client

CLIENT_NAME='course-discovery'


def course_discovery_api_client(user):
    """ Returns a Course Discovery API client setup with authentication for the specified user. """
    course_discovery_client = Client.objects.get(name=CLIENT_NAME)
    return EdxRestApiClient(
        course_discovery_client.url,
        jwt=get_id_token(user, CLIENT_NAME)
    )
