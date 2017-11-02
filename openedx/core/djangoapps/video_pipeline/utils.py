from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import JwtBuilder


def create_video_pipeline_api_client(user, api_url):
    """
    Returns an API client which can be used to make Video Pipeline API requests.

    Arguments:
        user(User): A requesting user.
        api_url(unicode): It is video pipeline's API URL.
    """
    jwt_token = JwtBuilder(user).build_token(
        scopes=[],
        expires_in=settings.OAUTH_ID_TOKEN_EXPIRATION
    )
    return EdxRestApiClient(api_url, jwt=jwt_token)
