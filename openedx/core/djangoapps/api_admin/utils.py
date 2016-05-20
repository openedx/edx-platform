""" Course Discovery API Service. """
from django.conf import settings

from edx_rest_api_client.client import EdxRestApiClient
from openedx.core.djangoapps.theming import helpers
from openedx.core.lib.token_utils import get_id_token
from provider.oauth2.models import Client

CLIENT_NAME = 'course-discovery'


def course_discovery_api_client(user):
    """ Returns a Course Discovery API client setup with authentication for the specified user. """
    course_discovery_client = Client.objects.get(name=CLIENT_NAME)
    secret_key = helpers.get_value('JWT_AUTH', settings.JWT_AUTH)['JWT_SECRET_KEY']
    return EdxRestApiClient(
        course_discovery_client.url,
        jwt=get_id_token(user, CLIENT_NAME, secret_key=secret_key)
    )
