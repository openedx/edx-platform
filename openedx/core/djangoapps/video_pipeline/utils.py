"""
Utils for video_pipeline app.
"""
from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import JwtBuilder


def create_video_pipeline_api_client(user, api_client_id, api_client_secret, api_url):
    """
    Returns an API client which can be used to make Video Pipeline API requests.

    Arguments:
        user(User): A requesting user.
        api_client_id(unicode): Video pipeline client id.
        api_client_secret(unicode): Video pipeline client secret.
        api_url(unicode): It is video pipeline's API URL.
    """
    jwt_token = JwtBuilder(user, secret=api_client_secret).build_token(
        scopes=[],
        expires_in=settings.OAUTH_ID_TOKEN_EXPIRATION,
        aud=api_client_id
    )
    return EdxRestApiClient(api_url, jwt=jwt_token)
