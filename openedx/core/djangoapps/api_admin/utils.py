""" Course Discovery API Service. """
import datetime

from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient
import jwt

from openedx.core.djangoapps.theming import helpers
from provider.oauth2.models import Client
from student.models import UserProfile, anonymous_id_for_user

CLIENT_NAME = 'course-discovery'


def get_id_token(user):
    """
    Return a JWT for `user`, suitable for use with the course discovery service.

    Arguments:
        user (User): User for whom to generate the JWT.

    Returns:
        str: The JWT.
    """
    try:
        # Service users may not have user profiles.
        full_name = UserProfile.objects.get(user=user).name
    except UserProfile.DoesNotExist:
        full_name = None

    now = datetime.datetime.utcnow()
    expires_in = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)

    payload = {
        'preferred_username': user.username,
        'name': full_name,
        'email': user.email,
        'administrator': user.is_staff,
        'iss': helpers.get_value('OAUTH_OIDC_ISSUER', settings.OAUTH_OIDC_ISSUER),
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
        'aud': helpers.get_value('JWT_AUTH', settings.JWT_AUTH)['JWT_AUDIENCE'],
        'sub': anonymous_id_for_user(user, None),
    }
    secret_key = helpers.get_value('JWT_AUTH', settings.JWT_AUTH)['JWT_SECRET_KEY']

    return jwt.encode(payload, secret_key)


def course_discovery_api_client(user):
    """ Returns a Course Discovery API client setup with authentication for the specified user. """
    course_discovery_client = Client.objects.get(name=CLIENT_NAME)
    return EdxRestApiClient(course_discovery_client.url, jwt=get_id_token(user))
